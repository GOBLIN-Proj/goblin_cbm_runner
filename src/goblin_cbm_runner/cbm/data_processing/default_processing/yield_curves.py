"""
Yield Curves Module
===================
This module is responsible for generating yield tables using different methods.

"""
from goblin_cbm_runner.resource_manager.loader import Loader
import math
import pandas as pd


class YieldCurves:
    """
    A class for generating yield tables using different methods.

    This class provides functionalities to generate yield tables based on various calculation methods. Yield tables are crucial in forest modeling to estimate the growth of forest stands over time.

    Methods:
        yield_table_generater_method1(): Generates a yield table using the first method based on parameters from a 'forest_kb_yields' dataset.
        yield_table_generater_method2(): Generates a yield table using the second method based on parameters from a 'forest_cbm_yields' dataset.
        yield_table_generater_method3(): Generates a yield table using the third method directly from 'kb_yield_curves' dataset.
        standing_vol_yield_table_generater_method(): Generates a standing volume table using the 'kb_standing_volume_curves' dataset.

    The generated yield tables are crucial for modeling forest growth and can be used in various simulation scenarios. Each method applies different mathematical models and parameters to estimate the yield over time for different forest cohorts.
    """

    @classmethod
    def yield_table_generater_method1(cls):
        """
        Generates a yield table using the first method.

        This method uses parameters from the 'forest_kb_yields' dataset and applies a specific growth formula to calculate yield for each year up to 100 years.

        Returns:
            DataFrame: A pandas DataFrame containing the yield for each species across 100 years.
        """
        # KB pg 444, NIR

        loader_class = Loader()
        parameters_df = loader_class.forest_kb_yields()

        index = parameters_df["Cohort"]

        cols = list(range(1, 101))

        yield_df = pd.DataFrame(index=index, columns=cols)

        for species in yield_df.index:
            param_mask = parameters_df["Cohort"] == species
            for year in yield_df.columns:
                a = parameters_df.loc[param_mask, "a"].values[0]
                b = parameters_df.loc[param_mask, "b"].values[0]
                c = parameters_df.loc[param_mask, "c"].values[0]
                if year != 1:
                    yield_df.loc[species, year] = yield_df.loc[species, year - 1] + (
                        a * math.exp(-b * year) * (1 - math.exp(-b * year)) ** (c - 1)
                    )
                else:
                    yield_df.loc[species, year] = (
                        a * math.exp(-b * year) * (1 - math.exp(-b * year)) ** (c - 1)
                    )

        return yield_df

    @classmethod
    def yield_table_generater_method2(cls):
        """
        Generates a yield table using the second method.

        This method uses parameters from the 'forest_cbm_yields' dataset and a different growth formula to calculate yield for each year up to 100 years.

        Returns:
            DataFrame: A pandas DataFrame containing the yield for each species across 100 years.
        """
        # CBM pg 444, NIR
        loader_class = Loader()
        parameters_df = loader_class.forest_cbm_yields()

        index = parameters_df["Cohort"]

        cols = list(range(1, 101))

        yield_df = pd.DataFrame(index=index, columns=cols)

        for species in yield_df.index:
            param_mask = parameters_df["Cohort"] == species
            for year in yield_df.columns:
                a = parameters_df.loc[param_mask, "a"].values[0]
                b = parameters_df.loc[param_mask, "b"].values[0]
                c = parameters_df.loc[param_mask, "c"].values[0]

                yield_df.loc[species, year] = a * (1 - math.exp(-b * year)) ** c

        return yield_df

    @classmethod
    def yield_table_generater_method3(cls):
        """
        Generates a yield table.

        This method directly uses the 'kb_yield_curves' dataset to provide yield data for various species across different years.

        Returns:
            DataFrame: A pandas DataFrame containing the yield data as per the kb_yield_curves dataset.
        """
        loader_class = Loader()
        yield_df = loader_class.kb_yield_curves()

        yield_df.columns = yield_df.columns.astype(int)

        return yield_df
    
    @classmethod
    def standing_vol_yield_table_generater_method(cls):
        """
        Generates a standing volume table.

        This method directly uses the 'kb_standing_volume_curves' dataset to provide data for various species across different years.

        Returns:
            DataFrame: A pandas DataFrame containing the standing volume data as per the kb_standing_volume_curves dataset.
        """
        loader_class = Loader()
        yield_df = loader_class.kb_standing_vol_yield_curves()

        yield_df.columns = yield_df.columns.astype(int)

        return yield_df
