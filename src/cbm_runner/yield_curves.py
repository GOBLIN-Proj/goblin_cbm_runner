from cbm_runner.loader import Loader
import math
import pandas as pd

class YieldCurves:


    @classmethod
    def yield_table_generater_method1(cls):

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