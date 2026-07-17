"""
Harvest Scheduler
=================
Determine which stands to harvest based on NAI and target harvest ratio.

The scheduler implements species-level sustainability:
- Calculates allowable harvest per species based on that species' NAI
- Uses Disturbance_timing table for species-specific age eligibility
- Splits harvest between clearfell (DISTID1) and thinning (DISTID2)
- Returns harvest targets that can be applied to CBM simulation

Disturbance Types:
- DISTID1 (Clearcut): Full harvest, stand age resets to 0
- DISTID2 (Thinning): Partial harvest, stand continues aging
"""
import pandas as pd
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class HarvestTarget:
    """A single harvest target for one stand."""
    stand_index: int
    disturbance_type: str  # e.g., 'DISTID1', 'DISTID2'
    area_proportion: float  # 0.0 to 1.0, proportion of stand area to disturb
    carbon_target: float  # tC to harvest from this stand


class HarvestScheduler:
    """
    Schedule harvests based on NAI and target harvest ratio.

    The scheduler works per-species to ensure species-level sustainability:
    - Each species has its own NAI
    - Each species has its own harvest target = harvest_ratio * NAI
    - Harvest is split between clearfell and thinning by configurable proportions
    - Stands are selected within each species based on Disturbance_timing rules

    Attributes:
        harvest_ratio: Target proportion of NAI to harvest (any positive value)
        clearfell_thinning_split: Dict mapping DISTID to proportion of harvest
        disturbance_timing: DataFrame with species-specific age eligibility
    """

    # Default disturbance type IDs
    CLEARFELL = 'DISTID1'
    THINNING = 'DISTID2'

    def __init__(
        self,
        harvest_ratio: float = 0.75,
        clearfell_thinning_split: Optional[dict] = None,
        disturbance_timing: Optional[pd.DataFrame] = None,
        species_column: str = 'Species',
        yield_class_column: str = 'Classifier4'
    ):
        """
        Initialize harvest scheduler.

        Args:
            harvest_ratio: Target proportion of NAI to harvest (default 0.75 = 75%)
                           Can be any positive value, including > 1.0 for testing
            clearfell_thinning_split: Dict mapping disturbance type to proportion
                           Default: {'DISTID1': 0.8, 'DISTID2': 0.2} (80% clearfell, 20% thin)
            disturbance_timing: DataFrame with columns: disturbance_id, sw_age_min,
                           sw_age_max, indexed by Cohort (species name)
                           If None, will use fallback defaults
            species_column: Column name containing species in classifiers DataFrame
            yield_class_column: Column name containing yield class (for timing lookup)
        """
        if harvest_ratio < 0:
            raise ValueError(f"harvest_ratio must be non-negative, got {harvest_ratio}")

        self.harvest_ratio = harvest_ratio
        self.clearfell_thinning_split = clearfell_thinning_split or {
            self.CLEARFELL: 0.8,
            self.THINNING: 0.2
        }
        self.disturbance_timing = disturbance_timing
        self.species_column = species_column
        self.yield_class_column = yield_class_column
        # Optional dict mapping integer classifier ID → species name string.
        # Set by DynamicRunner after extracting sit.classifier_value_names so
        # that get_eligibility() can look up Disturbance_timing (indexed by
        # cohort name) when libcbm classifiers contain integer IDs.
        self.species_name_map: dict = {}

        # Validate split proportions sum to ~1.0
        split_sum = sum(self.clearfell_thinning_split.values())
        if abs(split_sum - 1.0) > 0.01:
            raise ValueError(
                f"clearfell_thinning_split must sum to 1.0, got {split_sum}"
            )

    def get_eligibility(self, species: str, dist_type: str) -> tuple:
        """
        Get age eligibility window for a species and disturbance type.

        Args:
            species: Species name (Cohort in Disturbance_timing)
            dist_type: Disturbance type (DISTID1, DISTID2)

        Returns:
            Tuple (age_min, age_max) or (None, None) if not found
        """
        if self.disturbance_timing is None:
            # Fallback defaults if no timing table
            if dist_type == self.CLEARFELL:
                return (30, 200)
            elif dist_type == self.THINNING:
                return (15, 49)
            return (0, 200)

        # Resolve integer species ID → string name for Disturbance_timing lookup.
        # libcbm classifiers use integer IDs; Disturbance_timing is indexed by
        # cohort name (string).  Without this resolution, every lookup fails and
        # the fallback (0-200) is always used, allowing harvest of age-0 stands.
        lookup_species = species
        if isinstance(species, (int, float)) and self.species_name_map:
            lookup_species = self.species_name_map.get(int(species), species)

        try:
            timing_rows = self.disturbance_timing.loc[
                (self.disturbance_timing.index == lookup_species) &
                (self.disturbance_timing['disturbance_id'] == dist_type)
            ]
            if not timing_rows.empty:
                row = timing_rows.iloc[0]
                return (int(row['sw_age_min']), int(row['sw_age_max']))
        except (KeyError, ValueError):
            pass

        # Species not in table - return None to indicate unknown
        return (None, None)

    def compute_harvest_targets(
        self,
        nai_per_stand: pd.DataFrame,
        classifiers: pd.DataFrame,
        state: pd.DataFrame,
        inventory: pd.DataFrame,
        merch_stock_per_stand: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Compute harvest targets for the next timestep.

        Implements species-level sustainability:
        1. Group stands by species
        2. For each species, calculate total harvest target = harvest_ratio * species_NAI
        3. Split target between clearfell and thinning by configured proportions
        4. Select eligible stands (by age from Disturbance_timing) to meet targets

        Args:
            nai_per_stand: DataFrame with 'nai' column from NAICalculator
            classifiers: DataFrame with species classifier column
            state: DataFrame with 'age' column (from cbm_vars.state)
            inventory: DataFrame with 'area' column (from cbm_vars.inventory)
            merch_stock_per_stand: Optional Series with merchantable stock per stand

        Returns:
            DataFrame with columns:
                - stand_index: Index of stand to disturb
                - disturbance_type: 'DISTID1' (clearfell) or 'DISTID2' (thinning)
                - area_proportion: Proportion of stand area to disturb (0.0-1.0)
                - species: Species of the stand
                - nai_contribution: NAI from this stand
        """
        # Build working DataFrame
        df = pd.DataFrame({
            'stand_index': range(len(nai_per_stand)),
            'species': classifiers[self.species_column].values,
            'age': state['age'].values if hasattr(state['age'], 'values') else state['age'],
            'area': inventory['area'].values if hasattr(inventory['area'], 'values') else inventory['area'],
            'nai': nai_per_stand['nai'].values,
        })

        if merch_stock_per_stand is not None:
            df['merch_stock'] = merch_stock_per_stand.values
        else:
            df['merch_stock'] = df['nai'] * 10  # placeholder

        # Calculate harvest targets per species
        species_nai = df.groupby('species')['nai'].sum()
        species_total_targets = species_nai * self.harvest_ratio

        # Select stands to meet targets
        targets = []

        for species, total_target in species_total_targets.items():
            if total_target <= 0:
                continue

            # Split target between clearfell and thinning
            for dist_type, split_proportion in self.clearfell_thinning_split.items():
                type_target = total_target * split_proportion
                if type_target <= 0:
                    continue

                # Get age eligibility for this species and disturbance type
                age_min, age_max = self.get_eligibility(species, dist_type)

                if age_min is None:
                    # Species not in timing table - skip or use wide range
                    age_min, age_max = 0, 200

                # Get eligible stands for this species and disturbance type
                eligible_mask = (
                    (df['species'] == species) &
                    (df['age'] >= age_min) &
                    (df['age'] <= age_max) &
                    (df['nai'] > 0)
                )
                species_stands = df[eligible_mask].sort_values('age', ascending=False)

                if species_stands.empty:
                    continue

                remaining_target = type_target

                for _, stand in species_stands.iterrows():
                    if remaining_target <= 0:
                        break

                    stand_merch = stand['merch_stock']
                    stand_nai = stand['nai']

                    # Track target fulfillment by merch_stock (the actual
                    # volume removed by disturbance), not by NAI. The target
                    # = NAI × ratio represents the volume to harvest. Each
                    # clearfelled stand contributes its full merch_stock.
                    if stand_merch <= remaining_target:
                        area_proportion = 1.0
                        volume_contribution = stand_merch
                    else:
                        area_proportion = remaining_target / stand_merch
                        volume_contribution = remaining_target

                    targets.append({
                        'stand_index': int(stand['stand_index']),
                        'disturbance_type': dist_type,
                        'area_proportion': area_proportion,
                        'species': species,
                        'nai_contribution': stand_nai,
                        'volume_contribution': volume_contribution,
                        'age': stand['age']
                    })

                    remaining_target -= volume_contribution

        if not targets:
            return pd.DataFrame(columns=[
                'stand_index', 'disturbance_type', 'area_proportion',
                'species', 'nai_contribution', 'volume_contribution', 'age'
            ])

        return pd.DataFrame(targets)

    def summarize_targets(self, targets: pd.DataFrame) -> pd.DataFrame:
        """
        Summarize harvest targets by species.

        Args:
            targets: DataFrame from compute_harvest_targets()

        Returns:
            DataFrame with per-species summary:
                - stands_selected: Number of stands
                - total_nai_harvested: Total NAI being harvested
                - clearfell_count: Stands getting clearfelled
                - thinning_count: Stands getting thinned
        """
        if targets.empty:
            return pd.DataFrame()

        summary = targets.groupby('species').agg({
            'stand_index': 'count',
            'nai_contribution': 'sum',
            'area_proportion': 'mean'
        }).rename(columns={
            'stand_index': 'stands_selected',
            'nai_contribution': 'total_nai_harvested',
            'area_proportion': 'avg_area_proportion'
        })

        # Count by disturbance type
        clearfell_counts = targets[targets['disturbance_type'] == self.CLEARFELL].groupby('species').size()
        thinning_counts = targets[targets['disturbance_type'] == self.THINNING].groupby('species').size()

        summary['clearfell_count'] = clearfell_counts.reindex(summary.index, fill_value=0)
        summary['thinning_count'] = thinning_counts.reindex(summary.index, fill_value=0)

        return summary

    def validate_sustainability(
        self,
        targets: pd.DataFrame,
        nai_by_species: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Check harvest targets against NAI per species.

        Args:
            targets: DataFrame from compute_harvest_targets()
            nai_by_species: DataFrame from NAICalculator.calculate_nai_by_species()

        Returns:
            DataFrame with per-species validation:
                - nai: Total NAI for species
                - harvest_target: Planned harvest
                - harvest_ratio: Actual ratio
                - sustainable: True if harvest <= NAI
        """
        if targets.empty:
            return pd.DataFrame()

        harvest_by_species = targets.groupby('species')['nai_contribution'].sum()

        validation = pd.DataFrame({
            'nai': nai_by_species['nai'],
            'harvest_target': harvest_by_species.reindex(nai_by_species.index, fill_value=0)
        })

        validation['harvest_ratio'] = validation['harvest_target'] / validation['nai'].replace(0, np.nan)
        validation['sustainable'] = validation['harvest_target'] <= validation['nai']

        return validation
