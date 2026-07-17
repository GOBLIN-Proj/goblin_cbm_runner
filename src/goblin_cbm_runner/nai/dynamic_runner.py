"""
Dynamic Runner
==============
Stepwise CBM simulation with NAI-based harvest scheduling.

This runner allows continuing a simulation from an existing state (e.g., 2070)
with dynamic harvest based on Net Annual Increment, rather than pre-computed
disturbance schedules.

Key Features:
- Continue from any CBMVariables state
- Calculate NAI each timestep
- Schedule harvests based on NAI with configurable ratio
- Split harvest between clearfell/thinning by proportion
- Apply scheduled disturbances (fire, wind, etc.) from user input
- Track per-species sustainability metrics

Usage:
    from goblin_cbm_runner.nai import DynamicRunner
    from goblin_cbm_runner.resource_manager import Loader

    # Load disturbance timing from database
    disturbance_timing = Loader().disturbance_time()

    # Configure scheduled disturbances (fire, wind, etc.)
    scheduled_disturbances = [
        {'year': 2075, 'disturbance_type': 'DISTID3', 'area': 500},
        {'year': 2080, 'disturbance_type': 'DISTID3', 'area': 200},
    ]

    # Create runner
    runner = DynamicRunner(
        harvest_ratio=0.75,
        clearfell_thinning_split={'DISTID1': 0.8, 'DISTID2': 0.2},
        disturbance_timing=disturbance_timing,
        scheduled_disturbances=scheduled_disturbances
    )

    # Continue from FM simulation state
    result = runner.run_from_state(
        initial_cbm_vars=fm_final_state,
        sit=fm_sit,
        years=30,
        base_year=2070
    )
"""
import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from libcbm.input.sit import sit_cbm_factory
from libcbm.model.cbm.cbm_variables import CBMVariables
from libcbm.input.sit.sit import SIT
from libcbm.model.cbm.cbm_output import CBMOutput
from libcbm.storage.dataframe import from_pandas as libcbm_from_pandas

from goblin_cbm_runner.nai.nai_calculator import NAICalculator
from goblin_cbm_runner.nai.harvest_scheduler import HarvestScheduler
from goblin_cbm_runner.resource_manager import Pools
from goblin_cbm_runner.harvest_summary import HarvestSummaryBuilder


@dataclass
class ScheduledDisturbance:
    """
    A non-harvest disturbance to apply at a specific year.

    Use for fire (DISTID3), wind damage, or other scheduled events
    that are not based on NAI calculations.
    """
    year: int
    disturbance_type: str  # e.g., 'DISTID3' for fire
    area: float  # Total area to disturb (ha)
    # Optional filters
    species_filter: Optional[List[str]] = None  # Only affect these species
    age_min: Optional[int] = None  # Minimum stand age
    age_max: Optional[int] = None  # Maximum stand age


@dataclass
class DynamicSimulationResult:
    """Results from a dynamic simulation."""
    aggregated: pd.DataFrame  # Year, AGB, BGB, etc.
    nai_history: pd.DataFrame  # NAI per species per year
    harvest_history: pd.DataFrame  # Actual harvests per year
    scheduled_disturbance_history: pd.DataFrame  # Fire, wind, etc. applied
    sustainability_metrics: pd.DataFrame  # Harvest ratio validation
    validation_tables: Optional[dict] = field(default=None)
    harvest_summary: Optional[dict] = field(default=None)  # HarvestSummaryBuilder output


class DynamicRunner:
    """
    Run CBM simulation with dynamic NAI-based harvest.

    Unlike static runners (FM, AF, SC) that use pre-computed disturbance
    schedules from CSV files, DynamicRunner calculates harvest targets
    each timestep based on the previous year's Net Annual Increment.

    This enables:
    - Post-2070 simulation where no pre-computed harvests exist
    - Sustainable harvest enforcement (or testing unsustainable scenarios)
    - Configurable clearfell/thinning split
    - Scheduled non-harvest disturbances (fire, wind, etc.)
    """

    def __init__(
        self,
        harvest_ratio: float = 0.75,
        clearfell_thinning_split: Optional[dict] = None,
        disturbance_timing: Optional[pd.DataFrame] = None,
        scheduled_disturbances: Optional[List[dict]] = None,
        species_column: str = 'Species'
    ):
        """
        Initialize dynamic runner.

        Args:
            harvest_ratio: Target proportion of NAI to harvest.
                           Can be any non-negative value (e.g., 0.75, 1.0, 1.1)
            clearfell_thinning_split: Dict mapping disturbance type to proportion.
                           Default: {'DISTID1': 0.8, 'DISTID2': 0.2}
            disturbance_timing: DataFrame from Loader().disturbance_time()
                           Contains species-specific age windows for harvest.
                           If None, uses fallback defaults.
            scheduled_disturbances: List of dicts with keys:
                           year, disturbance_type, area, [species_filter], [age_min], [age_max]
                           For fire, wind, and other non-NAI-based disturbances.
            species_column: Column name containing species in classifiers DataFrame.
        """
        self.harvest_ratio = harvest_ratio
        self.clearfell_thinning_split = clearfell_thinning_split or {
            'DISTID1': 0.8,
            'DISTID2': 0.2
        }
        self.disturbance_timing = disturbance_timing
        self.species_column = species_column

        # Parse scheduled disturbances
        self.scheduled_disturbances = self._parse_scheduled_disturbances(
            scheduled_disturbances or []
        )

        # Initialize components
        self.nai_calc = NAICalculator()
        self.scheduler = HarvestScheduler(
            harvest_ratio=self.harvest_ratio,
            clearfell_thinning_split=self.clearfell_thinning_split,
            disturbance_timing=self.disturbance_timing,
            species_column=self.species_column
        )

        # Pool categorization for aggregation
        self._pools = Pools()
        self._AGB = self._pools.get_above_ground_biomass_pools()
        self._BGB = self._pools.get_below_ground_biomass_pools()
        self._deadwood = self._pools.get_deadwood_pools()
        self._litter = self._pools.get_litter_pools()
        self._soil = self._pools.get_soil_organic_matter_pools()

    def _parse_scheduled_disturbances(self, disturbances: List[dict]) -> dict:
        """
        Parse scheduled disturbances into year-indexed dict.

        Args:
            disturbances: List of dicts with year, disturbance_type, area, etc.

        Returns:
            Dict mapping year to list of ScheduledDisturbance objects
        """
        by_year = {}
        for d in disturbances:
            year = d['year']
            sd = ScheduledDisturbance(
                year=year,
                disturbance_type=d['disturbance_type'],
                area=d['area'],
                species_filter=d.get('species_filter'),
                age_min=d.get('age_min'),
                age_max=d.get('age_max')
            )
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(sd)
        return by_year

    def _compute_initial_targets(
        self,
        cbm_vars: CBMVariables,
        species_nai: Dict[int, float],
        dist_type_map: dict
    ) -> None:
        """
        Pre-compute harvest targets for the first dynamic timestep.

        Uses the standard pipeline's last-year per-species NAI to create
        synthetic per-stand NAI (distributed proportionally to merch_stock),
        then runs the normal harvest scheduling pipeline to set disturbance
        types on cbm_vars so that t=1 has realistic harvest.

        Args:
            cbm_vars: CBMVariables to modify (disturbance_type set in place)
            species_nai: Dict mapping species classifier ID (int) to total NAI (tC)
            dist_type_map: Disturbance type name to integer ID mapping
        """
        classifiers = self._extract_classifiers_df(cbm_vars)
        state = self._extract_state_df(cbm_vars)
        inventory = self._extract_inventory_df(cbm_vars)
        pools = self._extract_pools_df(cbm_vars)
        merch_stock = self.nai_calc.calculate_merch_stock(pools)

        # Build synthetic per-stand NAI by distributing each species' total NAI
        # proportionally to each stand's merch_stock within that species.
        species_col = classifiers[self.species_column].values
        n_stands = len(classifiers)
        synthetic_nai = pd.Series(0.0, index=range(n_stands))

        for sp_id, total_nai in species_nai.items():
            if total_nai <= 0:
                continue
            mask = species_col == sp_id
            sp_merch = merch_stock[mask]
            sp_total_merch = sp_merch.sum()
            if sp_total_merch > 0:
                synthetic_nai[mask] = total_nai * (sp_merch.values / sp_total_merch)

        nai_per_stand = pd.DataFrame({'nai': synthetic_nai})

        # Run the standard harvest scheduling pipeline
        harvest_targets = self.scheduler.compute_harvest_targets(
            nai_per_stand, classifiers, state, inventory, merch_stock
        )

        # Apply harvest disturbances to cbm_vars
        all_targets = self._combine_targets(harvest_targets, [])
        self._apply_disturbances(cbm_vars, all_targets, dist_type_map)

    def run_from_state(
        self,
        initial_cbm_vars: CBMVariables,
        sit: SIT,
        years: int,
        base_year: int = 2070,
        disturbance_type_map: Optional[dict] = None,
        capture_validation_tables: bool = False,
        cbm_vars_dump_dir: Optional[str] = None,
        initial_species_nai: Optional[Dict[int, float]] = None,
        spinup_warmup_steps: int = 0
    ) -> DynamicSimulationResult:
        """
        Continue simulation from existing CBMVariables state with dynamic harvest.

        Args:
            initial_cbm_vars: CBMVariables from end of previous simulation
                              (e.g., from FM runner at 2070)
            sit: SIT configuration (provides growth curves, AIDB reference)
            years: Number of years to simulate forward
            base_year: Calendar year corresponding to initial state
            disturbance_type_map: Map from DISTID names to integer IDs
                                  If None, will attempt to get from SIT
            capture_validation_tables: If True, capture detailed pools/flux/state
            cbm_vars_dump_dir: If set, write CBMVariables tables to CSV each timestep
            initial_species_nai: Optional dict mapping species classifier ID to NAI (tC).
                                 If provided, used to pre-compute harvest targets for
                                 the first timestep so t=1 has realistic harvest instead
                                 of zero harvest (which causes a flux spike at the
                                 transition year).
            spinup_warmup_steps: Number of growth-only (no-harvest) steps to advance the
                                 initial state before recording t=0. Defaults to 0.
                                 Use a small value (e.g. 3) when continuing from a fresh
                                 AF backward-decomposition spinup: that spinup over-inflates
                                 the Litter and Deadwood pools, and forward dynamics decay
                                 them sharply over the first few timesteps, producing
                                 spurious negative flux at the start of the series. Warming
                                 up lets those pools settle to (approximate) DOM equilibrium
                                 so the recorded initial state is clean. Leave at 0 when the
                                 initial state is already forward-simulated (e.g. the FM/AF
                                 2070 handoff), where no such artefact exists.

        Returns:
            DynamicSimulationResult with aggregated results and metrics
        """
        # Get disturbance type mapping
        dist_type_map = disturbance_type_map or self._get_disturbance_type_map(sit)

        # Build species name mapping from SIT classifier_value_names
        # This is a flat dict[int, str] mapping ALL classifier value IDs to names.
        # Species IDs (e.g., 1 -> 'Spruce13-16', 14 -> 'Cbmix-Bl') are a subset.
        self._species_name_map = {}
        if hasattr(sit, 'classifier_value_names') and sit.classifier_value_names:
            self._species_name_map = sit.classifier_value_names

        # Wire the species_name_map into the scheduler so that Disturbance_timing
        # lookups resolve integer classifier IDs → cohort name strings correctly.
        # Without this, all eligibility lookups fail and the scheduler falls back
        # to age_min=0/age_max=200, allowing harvest of age-0 stands.
        self.scheduler.species_name_map = self._species_name_map

        # Initialize output tracking
        cbm_output = CBMOutput(classifier_map=sit.classifier_value_names)

        # Track histories
        nai_history = []
        harvest_history = []
        scheduled_history = []

        # Current state
        cbm_vars = initial_cbm_vars

        # Clear any inherited disturbance types from previous simulation
        # (e.g., FM runner's last timestep may still have disturbances set)
        params_df = cbm_vars.parameters.to_pandas()
        params_df["disturbance_type"] = np.int32(0)
        cbm_vars.parameters = libcbm_from_pandas(params_df)

        # Optional spin-up warm-up: advance the pools a few steps (growth only,
        # no harvest) before recording t=0. The AF backward-decomposition spinup
        # over-inflates the Litter and Deadwood pools; forward dynamics decay them
        # sharply over the first ~3 timesteps, producing spurious negative flux at
        # the start of the series. Stepping forward here lets those pools settle so
        # the recorded initial state is at (approximate) DOM equilibrium. Defaults
        # to 0, so callers continuing from an already forward-simulated state (e.g.
        # the FM/AF 2070 handoff) are unaffected.
        for _ in range(max(0, spinup_warmup_steps)):
            cbm_vars = self._step_dynamics(sit, cbm_vars, 0)
        if spinup_warmup_steps > 0:
            params_df = cbm_vars.parameters.to_pandas()
            params_df["disturbance_type"] = np.int32(0)
            cbm_vars.parameters = libcbm_from_pandas(params_df)

        # Pre-compute harvest targets for t=1 using the standard pipeline's
        # last-year NAI. Without this, t=1 grows with zero harvest (disturbances
        # are cleared above), causing a massive flux spike at the transition year.
        if initial_species_nai:
            self._compute_initial_targets(cbm_vars, initial_species_nai, dist_type_map)

        prev_pools = self._extract_pools_df(cbm_vars)

        # Record initial state (t=0)
        cbm_output.append_simulation_result(0, cbm_vars)
        if cbm_vars_dump_dir:
            self._dump_cbm_vars(cbm_vars, cbm_vars_dump_dir, base_year, 0)

        print(f"Starting dynamic simulation: {base_year} to {base_year + years}")
        print(f"  Harvest ratio: {self.harvest_ratio}")
        print(f"  Clearfell/thinning split: {self.clearfell_thinning_split}")
        if self.scheduled_disturbances:
            print(f"  Scheduled disturbances: {len(self.scheduled_disturbances)} years with events")

        for t in range(1, years + 1):
            current_year = base_year + t

            # 1. Step forward (growth only, disturbances applied in previous step)
            cbm_vars = self._step_dynamics(sit, cbm_vars, t)

            # 2. Extract current pools
            curr_pools = self._extract_pools_df(cbm_vars)

            # 3. Extract harvest from flux (if any was applied last step)
            harvest_t = self._extract_harvest(cbm_vars)

            # 4. Calculate NAI
            classifiers = self._extract_classifiers_df(cbm_vars)
            nai_per_stand = self.nai_calc.calculate_nai_per_stand(
                prev_pools, curr_pools, harvest_t
            )
            nai_by_species = self.nai_calc.calculate_nai_by_species(
                prev_pools, curr_pools, classifiers,
                species_column=self.species_column,
                harvest_t1=harvest_t
            )

            # 5. Compute NAI-based harvest targets for NEXT timestep
            state = self._extract_state_df(cbm_vars)
            inventory = self._extract_inventory_df(cbm_vars)
            merch_stock = self.nai_calc.calculate_merch_stock(curr_pools)

            harvest_targets = self.scheduler.compute_harvest_targets(
                nai_per_stand, classifiers, state, inventory, merch_stock
            )

            # Record NAI with harvest info
            nai_record = nai_by_species.reset_index().rename(
                columns={'index': 'species'}
            )
            nai_record['year'] = current_year

            # Add harvest target info per species
            if not harvest_targets.empty:
                harvest_summary = self.scheduler.summarize_targets(harvest_targets)
                harvest_summary = harvest_summary.reset_index().rename(
                    columns={'index': 'species'}
                )
                # Merge volume targeted and disturbance counts
                harvest_by_species = harvest_targets.groupby('species').agg(
                    volume_targeted=('volume_contribution', 'sum'),
                    clearfell_stands=('disturbance_type', lambda x: (x == 'DISTID1').sum()),
                    thinning_stands=('disturbance_type', lambda x: (x == 'DISTID2').sum()),
                ).reset_index()
                nai_record = nai_record.merge(harvest_by_species, on='species', how='left')
            else:
                nai_record['volume_targeted'] = 0.0
                nai_record['clearfell_stands'] = 0
                nai_record['thinning_stands'] = 0

            nai_record['volume_targeted'] = nai_record['volume_targeted'].fillna(0.0)
            nai_record['clearfell_stands'] = nai_record['clearfell_stands'].fillna(0).astype(int)
            nai_record['thinning_stands'] = nai_record['thinning_stands'].fillna(0).astype(int)

            # Proportion of NAI targeted for harvest
            nai_record['harvest_proportion'] = nai_record.apply(
                lambda row: row['volume_targeted'] / row['nai'] if row['nai'] > 0 else 0.0,
                axis=1
            )

            # Map species integer IDs to descriptive names
            if self._species_name_map:
                nai_record['species_name'] = nai_record['species'].map(
                    self._species_name_map
                )
            else:
                nai_record['species_name'] = nai_record['species']

            # All NAI values are in tC of merchantable carbon (SoftwoodMerch + HardwoodMerch)
            nai_record['measurement_type'] = 'M'

            nai_history.append(nai_record)

            # Record planned harvest
            if not harvest_targets.empty:
                harvest_record = self.scheduler.summarize_targets(harvest_targets)
                harvest_record['year'] = current_year
                harvest_history.append(harvest_record)

            # 6. Get scheduled disturbances for this year (fire, wind, etc.)
            scheduled_targets = self._get_scheduled_targets(
                current_year, classifiers, state, inventory, dist_type_map
            )
            if scheduled_targets:
                scheduled_history.append({
                    'year': current_year,
                    'disturbances': scheduled_targets
                })

            # 7. Apply all disturbances to cbm_vars for next step
            all_targets = self._combine_targets(harvest_targets, scheduled_targets)
            self._apply_disturbances(cbm_vars, all_targets, dist_type_map)

            # Record results
            cbm_output.append_simulation_result(t, cbm_vars)
            if cbm_vars_dump_dir:
                self._dump_cbm_vars(cbm_vars, cbm_vars_dump_dir, current_year, t)

            # Update for next iteration
            prev_pools = curr_pools

            if t % 10 == 0:
                print(f"  Year {current_year} complete")

        print(f"Dynamic simulation complete: {years} years")

        # Extract disturbance maps from SIT for harvest summary
        disturbance_id_map = getattr(sit, 'disturbance_id_map', None)
        disturbance_name_map = getattr(sit, 'disturbance_name_map', None)

        # Build result
        return self._build_result(
            cbm_output, base_year, years,
            nai_history, harvest_history, scheduled_history,
            capture_validation_tables,
            disturbance_id_map=disturbance_id_map,
            disturbance_name_map=disturbance_name_map
        )

    def _dump_cbm_vars(
        self,
        cbm_vars: CBMVariables,
        dump_dir: str,
        year: int,
        timestep: int
    ) -> None:
        """
        Write CBMVariables tables to CSV for inspection.

        Creates files like pools_year_2070_t0000.csv in the dump directory.
        """
        os.makedirs(dump_dir, exist_ok=True)

        tables = {
            "pools": cbm_vars.pools,
            "flux": cbm_vars.flux,
            "state": cbm_vars.state,
            "parameters": cbm_vars.parameters,
            "classifiers": cbm_vars.classifiers,
            "inventory": cbm_vars.inventory,
        }

        for name, table in tables.items():
            if table is None:
                continue
            df = table.to_pandas()
            filename = f"{name}_year_{year}_t{timestep:04d}.csv"
            df.to_csv(os.path.join(dump_dir, filename), index=False)

    def _step_dynamics(self, sit: SIT, cbm_vars: CBMVariables, timestep: int) -> CBMVariables:
        """
        Step CBM dynamics forward one year.

        Unlike the static step() that uses rule_based_processor to apply
        disturbances from CSV files, this applies whatever disturbances
        are already set in cbm_vars.parameters['disturbance_type'].
        """
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            cbm_vars = cbm.step(cbm_vars)
            return cbm_vars

    def _get_scheduled_targets(
        self,
        year: int,
        classifiers: pd.DataFrame,
        state: pd.DataFrame,
        inventory: pd.DataFrame,
        dist_type_map: dict
    ) -> List[dict]:
        """
        Get targets for scheduled disturbances (fire, wind, etc.) for this year.

        Args:
            year: Current calendar year
            classifiers: Stand classifiers
            state: Stand state (age, etc.)
            inventory: Stand inventory (area, etc.)
            dist_type_map: Disturbance type name to ID mapping

        Returns:
            List of target dicts with stand_index, disturbance_type, area_proportion
        """
        if year not in self.scheduled_disturbances:
            return []

        targets = []

        for sd in self.scheduled_disturbances[year]:
            # Build eligibility mask
            n_stands = len(classifiers)
            eligible = pd.Series(True, index=range(n_stands))

            # Apply species filter if specified
            if sd.species_filter:
                eligible &= classifiers[self.species_column].isin(sd.species_filter)

            # Apply age filters if specified
            ages = state['age'].values if hasattr(state['age'], 'values') else state['age']
            if sd.age_min is not None:
                eligible &= pd.Series(ages) >= sd.age_min
            if sd.age_max is not None:
                eligible &= pd.Series(ages) <= sd.age_max

            # Get eligible stands
            eligible_indices = eligible[eligible].index.tolist()
            if not eligible_indices:
                continue

            # Calculate area per eligible stand
            areas = inventory['area'].values if hasattr(inventory['area'], 'values') else inventory['area']
            eligible_areas = pd.Series(areas)[eligible_indices]
            total_eligible_area = eligible_areas.sum()

            if total_eligible_area <= 0:
                continue

            # Distribute disturbance area uniformly across eligible stands
            area_to_disturb = min(sd.area, total_eligible_area)
            area_proportion = area_to_disturb / total_eligible_area

            for idx in eligible_indices:
                targets.append({
                    'stand_index': idx,
                    'disturbance_type': sd.disturbance_type,
                    'area_proportion': area_proportion,
                    'source': 'scheduled'
                })

        return targets

    def _combine_targets(
        self,
        harvest_targets: pd.DataFrame,
        scheduled_targets: List[dict]
    ) -> pd.DataFrame:
        """
        Combine NAI-based harvest targets with scheduled disturbances.

        If a stand has both harvest and scheduled disturbance, the scheduled
        disturbance takes precedence (fire destroys before harvest).
        """
        if harvest_targets.empty and not scheduled_targets:
            return pd.DataFrame(columns=[
                'stand_index', 'disturbance_type', 'area_proportion'
            ])

        all_targets = []

        # Add harvest targets
        if not harvest_targets.empty:
            for _, row in harvest_targets.iterrows():
                all_targets.append({
                    'stand_index': int(row['stand_index']),
                    'disturbance_type': row['disturbance_type'],
                    'area_proportion': row['area_proportion'],
                    'source': 'harvest'
                })

        # Add scheduled targets (may override harvest)
        scheduled_stands = set()
        for target in scheduled_targets:
            scheduled_stands.add(target['stand_index'])
            all_targets.append(target)

        # Remove harvest targets for stands that have scheduled disturbances
        all_targets = [
            t for t in all_targets
            if t['source'] == 'scheduled' or t['stand_index'] not in scheduled_stands
        ]

        return pd.DataFrame(all_targets)

    def _apply_disturbances(
        self,
        cbm_vars: CBMVariables,
        targets: pd.DataFrame,
        dist_type_map: dict
    ) -> None:
        """
        Apply disturbance targets by setting disturbance_type in cbm_vars.parameters.

        For harvest targets (source='harvest'), only applies to stands with
        area_proportion >= 1.0. libcbm's cbm.step() applies disturbance to
        100% of a stand — there is no partial-area mechanism. Applying harvest
        to partial stands would remove far more carbon than the scheduler
        intended. Skipping partial harvest stands means we slightly under-harvest
        relative to the target, which is the conservative choice.

        Scheduled disturbances (source='scheduled') are always applied regardless
        of area_proportion — fire and wind affect the full stand.

        Args:
            cbm_vars: CBM variables to modify (in place)
            targets: DataFrame with stand_index, disturbance_type, area_proportion
            dist_type_map: Map from DISTID names to integer IDs
        """
        if targets.empty:
            return

        # Reset all disturbance types to 0, then apply targets
        params_df = cbm_vars.parameters.to_pandas()
        params_df["disturbance_type"] = np.int32(0)

        for _, row in targets.iterrows():
            # Apply all harvest targets. libcbm clearfells 100% of the selected
            # stand regardless of area_proportion. If a stand's merch_stock
            # exceeds the NAI-based target for that timestep, the next year's
            # NAI formula self-corrects (lower stock → lower target). Skipping
            # partial targets caused systematic under-harvest (~60% fulfillment).
            source = row.get('source', 'harvest')

            stand_idx = int(row['stand_index'])
            dist_type_name = row['disturbance_type']
            dist_type_id = dist_type_map.get(dist_type_name, 0)

            if dist_type_id > 0:
                params_df.loc[stand_idx, "disturbance_type"] = np.int32(dist_type_id)

        cbm_vars.parameters = libcbm_from_pandas(params_df)

    def _get_disturbance_type_map(self, sit: SIT) -> dict:
        """
        Extract disturbance type name to ID mapping from SIT.

        Builds a mapping that supports both naming conventions:
        - SIT display names: 'Clearcut', 'Thinning', 'Fire', etc.
        - DISTID names: 'DISTID1', 'DISTID2', 'DISTID3', etc.

        The SIT disturbance_name_map provides {integer_id: display_name}.
        The DISTID names follow the pattern DISTIDn where n = integer_id.
        Both are included so that code using either convention works.

        Returns:
            Dict mapping disturbance names to integer IDs.
            E.g., {'Clearcut': 1, 'DISTID1': 1, 'Thinning': 2, 'DISTID2': 2, ...}
        """
        dist_map = {}

        if hasattr(sit, 'disturbance_name_map') and sit.disturbance_name_map:
            for int_id, name in sit.disturbance_name_map.items():
                if int_id > 0:
                    # Add SIT display name (e.g., 'Clearcut' → 1)
                    if name:
                        dist_map[name] = int_id
                    # Add DISTID name (e.g., 'DISTID1' → 1)
                    dist_map[f'DISTID{int_id}'] = int_id
        else:
            # Fallback: DISTID names only
            for i in range(1, 8):
                dist_map[f'DISTID{i}'] = i

        return dist_map

    def _extract_pools_df(self, cbm_vars: CBMVariables) -> pd.DataFrame:
        """Extract pools as pandas DataFrame.

        Uses .copy() because libcbm's to_pandas() may return a DataFrame
        backed by shared memory with the internal pool arrays. Without
        copy, cbm.step() silently mutates previously-extracted DataFrames,
        causing NAI to compute as zero (prev_pools == curr_pools).
        """
        return cbm_vars.pools.to_pandas().copy()

    def _extract_classifiers_df(self, cbm_vars: CBMVariables) -> pd.DataFrame:
        """Extract classifiers as pandas DataFrame."""
        return cbm_vars.classifiers.to_pandas()

    def _extract_state_df(self, cbm_vars: CBMVariables) -> pd.DataFrame:
        """Extract state as pandas DataFrame."""
        return cbm_vars.state.to_pandas()

    def _extract_inventory_df(self, cbm_vars: CBMVariables) -> pd.DataFrame:
        """Extract inventory as pandas DataFrame."""
        return cbm_vars.inventory.to_pandas()

    def _extract_harvest(self, cbm_vars: CBMVariables) -> pd.Series:
        """
        Extract harvest carbon from flux data.

        libcbm records harvested carbon in flux indicators:
        - DisturbanceSoftProduction: Softwood harvest
        - DisturbanceHardProduction: Hardwood harvest
        - DisturbanceDOMProduction: Harvest from standing dead trees (KB: add
          this to merchantable C values before volume conversion)

        Returns:
            Series with total harvest carbon per stand
        """
        flux_df = cbm_vars.flux.to_pandas()

        harvest = pd.Series(0.0, index=range(len(flux_df)))

        if 'DisturbanceSoftProduction' in flux_df.columns:
            harvest += flux_df['DisturbanceSoftProduction'].values

        if 'DisturbanceHardProduction' in flux_df.columns:
            harvest += flux_df['DisturbanceHardProduction'].values

        if 'DisturbanceDOMProduction' in flux_df.columns:
            harvest += flux_df['DisturbanceDOMProduction'].values

        return harvest

    def _build_result(
        self,
        cbm_output: CBMOutput,
        base_year: int,
        years: int,
        nai_history: list,
        harvest_history: list,
        scheduled_history: list,
        capture_validation: bool,
        disturbance_id_map: Optional[dict] = None,
        disturbance_name_map: Optional[dict] = None
    ) -> DynamicSimulationResult:
        """Build the simulation result from collected data."""

        # Extract pools and classifiers
        pools_df = cbm_output.pools.to_pandas()
        classifiers_df = cbm_output.classifiers.to_pandas()

        # Merge for aggregation
        pi = classifiers_df.merge(
            pools_df,
            left_on=["identifier", "timestep"],
            right_on=["identifier", "timestep"]
        )

        # Calculate aggregated stocks
        annual_stocks = pd.DataFrame({
            "Year": pi["timestep"],
            "AGB": pi[self._AGB].sum(axis=1),
            "BGB": pi[self._BGB].sum(axis=1),
            "Deadwood": pi[self._deadwood].sum(axis=1),
            "Litter": pi[self._litter].sum(axis=1),
            "Soil": pi[self._soil].sum(axis=1),
            "Harvest": pi["Products"],
            "Total Ecosystem": pi[
                self._AGB + self._BGB + self._deadwood + self._litter + self._soil
            ].sum(axis=1),
        })

        annual_stocks = annual_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        ].sum()

        # Convert timesteps to calendar years
        year_range = list(range(base_year, base_year + years + 1))
        annual_stocks["Year"] = year_range

        # Combine NAI history (species is a column, not index)
        nai_df = pd.concat(nai_history, ignore_index=True) if nai_history else pd.DataFrame()

        # Combine harvest history
        harvest_df = pd.concat(harvest_history, ignore_index=False) if harvest_history else pd.DataFrame()

        # Build scheduled disturbance history
        scheduled_df = pd.DataFrame(scheduled_history) if scheduled_history else pd.DataFrame()

        # Calculate sustainability metrics
        sustainability = self._calculate_sustainability_metrics(nai_df, harvest_df)

        # Build harvest summary (always-on, matches HarvestSummaryBuilder format)
        harvest_summary = None
        try:
            harvest_summary = HarvestSummaryBuilder.build(
                cbm_output=cbm_output,
                year_range=year_range,
                disturbance_id_map=disturbance_id_map,
                disturbance_name_map=disturbance_name_map,
            )
        except Exception as e:
            print(f"Warning: Could not build harvest summary for dynamic continuation: {e}")

        # Validation tables
        validation = None
        if capture_validation:
            validation = {
                'pools': pools_df,
                'flux': cbm_output.flux.to_pandas(),
                'state': cbm_output.state.to_pandas(),
                'area': cbm_output.area.to_pandas(),
                'parameters': cbm_output.parameters.to_pandas(),
                'classifiers': classifiers_df,
            }

        return DynamicSimulationResult(
            aggregated=annual_stocks,
            nai_history=nai_df,
            harvest_history=harvest_df,
            scheduled_disturbance_history=scheduled_df,
            sustainability_metrics=sustainability,
            validation_tables=validation,
            harvest_summary=harvest_summary,
        )

    def _calculate_sustainability_metrics(
        self,
        nai_df: pd.DataFrame,
        harvest_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate sustainability metrics over the simulation period."""
        if nai_df.empty:
            return pd.DataFrame()

        # Use species column (may be column or index depending on source)
        if 'species' in nai_df.columns:
            species_list = nai_df['species'].unique()
        else:
            species_list = nai_df.index.unique()

        species_metrics = []

        for species in species_list:
            # Get total NAI for this species
            if 'species' in nai_df.columns:
                total_nai = nai_df.loc[nai_df['species'] == species, 'nai'].sum()
            else:
                species_nai = nai_df.loc[species]
                total_nai = species_nai['nai'] if isinstance(species_nai, pd.Series) else species_nai['nai'].sum()

            # Get total volume targeted for harvest
            total_harvest_volume = 0.0
            if 'volume_targeted' in nai_df.columns:
                total_harvest_volume = nai_df.loc[
                    nai_df['species'] == species, 'volume_targeted'
                ].sum()
            elif not harvest_df.empty and species in harvest_df.index:
                species_harvest = harvest_df.loc[species]
                if isinstance(species_harvest, pd.Series):
                    total_harvest_volume = species_harvest.get('total_nai_harvested', 0.0)
                else:
                    total_harvest_volume = species_harvest['total_nai_harvested'].sum()

            ratio = total_harvest_volume / total_nai if total_nai > 0 else 0.0

            # Get species name from nai_df if available
            species_name = species
            if 'species_name' in nai_df.columns:
                name_vals = nai_df.loc[nai_df['species'] == species, 'species_name']
                if not name_vals.empty:
                    species_name = name_vals.iloc[0]

            species_metrics.append({
                'species': species,
                'species_name': species_name,
                'total_nai': total_nai,
                'total_harvest_volume': total_harvest_volume,
                'avg_harvest_ratio': ratio,
                'sustainable': ratio <= 1.0
            })

        return pd.DataFrame(species_metrics)
