import pandas as pd
import os
import cbm_runner.parser as parser
from cbm_runner.loader import Loader
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.yield_curves import YieldCurves


class Harvest:
    def __init__(self, config_path):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(config_path)
        self.baseline_forest_classifiers = self.data_manager_class.classifiers[
            "Baseline"
        ]

    def get_harvest_areas(self):
        forest_harvest = self.loader_class.harvest_areas_NIR()

        yield_dict = self.make_yields()

        yield_proportions_list = self.baseline_forest_classifiers["Yield_class"]["CF"]
        yield_proportions_dict = {
            list(yield_proportions_list[i].keys())[0]: list(
                yield_proportions_list[i].values()
            )[0]
            for i, _ in enumerate(yield_proportions_list)
        }

        soils_proprotions = self.generate_soil_proportions()

        cols = ["year", "yield_class", "mineral", "peat"]

        harvest_area = pd.DataFrame(columns=cols)

        count = 0
        for year in forest_harvest.index:
            for yc in yield_dict.keys():
                proportion = yield_proportions_dict[yc]
                volumn = forest_harvest.at[year, "production_m3"]
                yield_volumns = yield_dict[yc]

                harvest_area.at[count, "year"] = year
                harvest_area.at[count, "yield_class"] = yc
                harvest_area.at[count, "mineral"] = (
                    self.calculate_area(proportion, volumn, yield_volumns)
                    * soils_proprotions.at[year, "mineral"]
                )
                harvest_area.at[count, "peat"] = (
                    self.calculate_area(proportion, volumn, yield_volumns)
                    * soils_proprotions.at[year, "organic"]
                )

                count += 1

        return harvest_area

    def calculate_area(self, proportion, harvest_volumn, yield_volumns):
        return (harvest_volumn * proportion) / yield_volumns

    def generate_soil_proportions(self):
        forest_inventory = self.loader_class.NIR_forest_data_ha()

        cols = ["mineral", "organic"]
        soils_proportion = pd.DataFrame(index=forest_inventory.index, columns=cols)

        soils_proportion["mineral"] = (
            forest_inventory["mineral_kha"] / forest_inventory["total_kha"]
        )
        soils_proportion["organic"] = (
            forest_inventory["organic_kha"] / forest_inventory["total_kha"]
        )

        return soils_proportion

    def make_yields(self):
        yield_table = YieldCurves.yield_table_generater_method1()
        harvest_dict = self.data_manager_class.forest_baseline_disturbance_dict

        yield_names = self.data_manager_class.yield_name_dict

        volumes = {}

        for yield_name in yield_names["Sitka"].keys():
            mask = yield_table.index == yield_names["Sitka"][yield_name]

            col = harvest_dict["DISTID1"]["Sitka"][yield_names["Sitka"][yield_name]]

            if col is not None:
                volumes[yield_name] = yield_table.loc[mask, col].item()

        return volumes
