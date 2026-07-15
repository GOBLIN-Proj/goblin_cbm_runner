"""
NAI Calculator
==============
Calculate Net Annual Increment (NAI) from CBM pool data.

NAI represents the net growth of merchantable wood in one year.
It is used to determine sustainable harvest levels.

Formula (Kevin Black):
    NAI = MerchStock[t+1] - MerchStock[t] + Harvest[t+1]

This formula accounts for harvest: the stock change alone understates
growth because harvested wood is removed from the stock.

Example:
    Year 2070: MerchStock = 100 tC
    During 2070: Growth = +5 tC, Harvest = 3 tC
    Year 2071: MerchStock = 102 tC

    NAI = 102 - 100 + 3 = 5 tC  (equals the growth)
"""
import pandas as pd
from typing import Optional


class NAICalculator:
    """
    Calculate Net Annual Increment from CBM pool data.

    NAI can be calculated:
    - Per stand (for detailed analysis)
    - Per species (for species-level sustainability)
    - Aggregate (for national totals)

    Attributes:
        merch_pools: List of pool column names that constitute merchantable stock.
                     Default: ['SoftwoodMerch', 'HardwoodMerch']
    """

    # Default merchantable pool columns in libcbm
    DEFAULT_MERCH_POOLS = ['SoftwoodMerch', 'HardwoodMerch']

    def __init__(self, merch_pools: Optional[list[str]] = None):
        """
        Initialize NAI calculator.

        Args:
            merch_pools: Pool columns to sum for merchantable stock.
                         If None, uses DEFAULT_MERCH_POOLS.
        """
        self.merch_pools = merch_pools if merch_pools is not None else self.DEFAULT_MERCH_POOLS

    def calculate_merch_stock(self, pools_df: pd.DataFrame) -> pd.Series:
        """
        Calculate total merchantable stock per stand.

        Args:
            pools_df: DataFrame with pool columns. Each row is a stand.

        Returns:
            Series with merchantable stock per stand (sum of merch pools).

        Raises:
            KeyError: If required pool columns are missing.
        """
        missing = [p for p in self.merch_pools if p not in pools_df.columns]
        if missing:
            raise KeyError(f"Missing pool columns: {missing}. Available: {list(pools_df.columns)}")

        return pools_df[self.merch_pools].sum(axis=1)

    def calculate_nai_per_stand(
        self,
        pools_t0: pd.DataFrame,
        pools_t1: pd.DataFrame,
        harvest_t1: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calculate NAI for each stand between two timesteps.

        NAI = MerchStock[t1] - MerchStock[t0] + Harvest[t1]

        Args:
            pools_t0: Pool values at start of period (timestep t).
            pools_t1: Pool values at end of period (timestep t+1).
            harvest_t1: Harvest that occurred during the period (optional).
                        If None, assumes no harvest (returns gross growth).

        Returns:
            DataFrame with columns:
                - merch_t0: Merchantable stock at t0
                - merch_t1: Merchantable stock at t1
                - stock_change: merch_t1 - merch_t0
                - harvest: Harvest during period (0 if not provided)
                - nai: Net Annual Increment

        Note:
            Rows in pools_t0 and pools_t1 must be aligned (same stand order).
        """
        merch_t0 = self.calculate_merch_stock(pools_t0)
        merch_t1 = self.calculate_merch_stock(pools_t1)

        stock_change = merch_t1 - merch_t0

        if harvest_t1 is not None:
            harvest = harvest_t1
            nai = stock_change + harvest
        else:
            harvest = pd.Series(0.0, index=merch_t0.index)
            nai = stock_change  # Without harvest, NAI = stock change = gross growth

        return pd.DataFrame({
            'merch_t0': merch_t0,
            'merch_t1': merch_t1,
            'stock_change': stock_change,
            'harvest': harvest,
            'nai': nai
        })

    def calculate_nai_by_species(
        self,
        pools_t0: pd.DataFrame,
        pools_t1: pd.DataFrame,
        classifiers: pd.DataFrame,
        species_column: str = 'Species',
        harvest_t1: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calculate NAI aggregated by species.

        Args:
            pools_t0: Pool values at start of period.
            pools_t1: Pool values at end of period.
            classifiers: DataFrame with classifier columns (must include species_column).
            species_column: Column name containing species identifier.
            harvest_t1: Harvest that occurred during the period (optional).

        Returns:
            DataFrame indexed by species with columns:
                - merch_t0: Total merchantable stock at t0
                - merch_t1: Total merchantable stock at t1
                - stock_change: Total stock change
                - harvest: Total harvest
                - nai: Total NAI
                - stand_count: Number of stands of this species
        """
        # Calculate per-stand NAI
        stand_nai = self.calculate_nai_per_stand(pools_t0, pools_t1, harvest_t1)

        # Add species column
        stand_nai['species'] = classifiers[species_column].values

        # Aggregate by species
        species_nai = stand_nai.groupby('species').agg({
            'merch_t0': 'sum',
            'merch_t1': 'sum',
            'stock_change': 'sum',
            'harvest': 'sum',
            'nai': 'sum'
        })

        # Add stand count
        species_nai['stand_count'] = stand_nai.groupby('species').size()

        return species_nai

    def calculate_nai_aggregate(
        self,
        pools_t0: pd.DataFrame,
        pools_t1: pd.DataFrame,
        harvest_t1: Optional[pd.Series] = None
    ) -> dict:
        """
        Calculate total NAI across all stands.

        Args:
            pools_t0: Pool values at start of period.
            pools_t1: Pool values at end of period.
            harvest_t1: Harvest that occurred during the period (optional).

        Returns:
            Dict with:
                - merch_t0: Total merchantable stock at t0
                - merch_t1: Total merchantable stock at t1
                - stock_change: Total stock change
                - harvest: Total harvest
                - nai: Total NAI
                - stand_count: Number of stands
        """
        stand_nai = self.calculate_nai_per_stand(pools_t0, pools_t1, harvest_t1)

        return {
            'merch_t0': stand_nai['merch_t0'].sum(),
            'merch_t1': stand_nai['merch_t1'].sum(),
            'stock_change': stand_nai['stock_change'].sum(),
            'harvest': stand_nai['harvest'].sum(),
            'nai': stand_nai['nai'].sum(),
            'stand_count': len(stand_nai)
        }

    def calculate_harvest_ratio(self, harvest: float, nai: float) -> float:
        """
        Calculate harvest ratio (harvest as proportion of NAI).

        Args:
            harvest: Amount harvested (tC)
            nai: Net Annual Increment (tC)

        Returns:
            Harvest ratio (0.0 to infinity).
            Returns 0.0 if NAI is zero or negative (no growth to harvest).

        Interpretation:
            - ratio < 1.0: Sustainable (harvesting less than growth)
            - ratio = 1.0: Steady state (harvest equals growth)
            - ratio > 1.0: Unsustainable (harvesting more than growth)
        """
        if nai <= 0:
            return 0.0
        return harvest / nai
