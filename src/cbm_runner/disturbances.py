import cbm_runner.parser as parser
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.loader import Loader
from cbm_runner.inventory import Inventory
from cbm_runner.harvest import Harvest
import pandas as pd
import itertools
from collections import defaultdict


class Distrubances:
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        scenario_data,
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
        self.loader_class = Loader()
        self.data_manager_class = DataManager(
            calibration_year, config_path, scenario_data
        )
        self.baseline_forest_classifiers = self.data_manager_class.classifiers[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.classifiers[
            "Scenario"
        ]
        self.afforestation_data = afforestation_data
        self.inventory_class = Inventory(
            calibration_year, config_path, afforestation_data
        )
        # self.harvest_class = Harvest(config_path)

    def scenario_afforestation_area(self, scenario):
        scenario_years = self.forest_end_year - self.calibration_year

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        for species in parser.get_inventory_species(classifiers):
            mask = (self.afforestation_data["species"] == species) & (
                self.afforestation_data["scenario"] == scenario
            )

            result_dict[species] = {}
            result_dict[species]["mineral"] = (
                self.afforestation_data.loc[mask, "total_area"].item() / scenario_years
            )

        return result_dict

    def legacy_disturbance_afforestation_area(self, scenario, years):
        years = list(range(1, years + 1))

        result_dataframe = pd.DataFrame()

        classifiers = self.scenario_forest_classifiers
        year_index = self.data_manager_class.afforestation_baseline - 1

        afforestation_mineral = self.inventory_class.legacy_afforestation_annual()[
            "mineral_afforestation"
        ]
        afforestation_organic = self.inventory_class.legacy_afforestation_annual()[
            "peat_afforestation"
        ]

        yield_dict = self.data_manager_class.yield_basline_dict

        year_count = 1
        index = 0

        for species in classifiers["Species"].keys():
            if species in yield_dict.keys():
                for yield_class in yield_dict[species].keys():
                    for soil_class in classifiers["Soil classes"].keys():
                        for i in years:
                            result_dataframe.at[index, "year"] = year_count
                            result_dataframe.at[index, "species"] = species
                            result_dataframe.at[index, "yield_class"] = yield_class
                            result_dataframe.at[index, "soil"] = soil_class

                            if soil_class == "peat":
                                result_dataframe.at[
                                    index, "area_ha"
                                ] = afforestation_organic[year_index + year_count][
                                    species
                                ][
                                    yield_class
                                ]

                            else:
                                result_dataframe.at[
                                    index, "area_ha"
                                ] = afforestation_mineral[year_index + year_count][
                                    species
                                ][
                                    yield_class
                                ]

                            index += 1
                            year_count += 1

                        year_count = 1

        return result_dataframe

    def legacy_disturbance_calculation(
        self, legacy_value, yield_class, age_ids, disturbance_proprtion
    ):
        age_df = self.loader_class.forest_age_structure()
        classifiers = self.classifiers

        result = 0

        yield_list = parser.get_yield_class(classifiers, "CF")
        yield_dict = {
            list(yield_list[i].keys())[0]: list(yield_list[i].values())[0]
            for i, _ in enumerate(yield_list)
        }

        age = parser.get_age_classifier(classifiers)

        for ID in age_ids:
            age_mask = age_df["year"] == age[ID]

            result += (
                legacy_value
                * yield_dict[yield_class]
                * age_df.loc[age_mask, "aggregate"].values
                * disturbance_proprtion
            )

        return result[0]

    def disturbance_structure(self):
        columns = self.data_manager_class.disturbance_cols
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df

    def fill_legacy_data(self, scenario):
        classifiers = self.scenario_forest_classifiers
        disturbances = self.data_manager_class.disturbances_config["Scenario"]

        forest_baseline_year = self.data_manager_class.afforestation_baseline

        yield_name_dict = self.data_manager_class.yield_name_dict

        static_cols = self.data_manager_class.static_disturbance_cols

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()
        disturbance_dataframe = self.loader_class.disturbance_data()

        legacy_years = calibration_year - forest_baseline_year

        legacy_afforestation_inventory = self.legacy_disturbance_afforestation_area(
            scenario, legacy_years
        )

        non_forest_dict = self.data_manager_class.non_forest_dict

        yield_name = self.data_manager_class.yield_name_dict

        disturbance_timing = self.loader_class.disturbance_time()

        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        static_defaults = {col: -1 for col in static_cols}

        data = []

        for yr in range(1, (legacy_years + 1)):
            for dist in disturbances:
                for species in yield_name_dict.keys():
                    classifier_combo = itertools.product(
                        forest_keys, soil_keys, yield_keys
                    )

                    for combination in classifier_combo:
                        forest_type, soil, yield_class = combination

                        row_data = {
                            "Classifier1": species,
                            "Classifier2": forest_type,
                            "Classifier3": soil,
                            "Classifier4": yield_class,
                            "UsingID": False,
                            "sw_age_min": 0,
                            "sw_age_max": 210,
                            "hw_age_min": 0,
                            "hw_age_max": 210,
                            "MinYearsSinceDist": -1,
                            **static_defaults,
                            "Efficiency": 1,
                            "SortType": 3,
                            "MeasureType": "A",
                            "Amount": 0,
                            "DistTypeID": dist,
                            "Year": yr,
                        }

                        if (
                            species in yield_name.keys()
                            and yield_class in yield_name[species].keys()
                        ):
                            try:
                                sw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_min",
                                ].item()
                                sw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_max",
                                ].item()
                                hw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_min",
                                ].item()
                                hw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_max",
                                ].item()
                                min_years = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "min years since dist",
                                ].item()

                                row_data["sw_age_min"] = int(sw_min)
                                row_data["sw_age_max"] = int(sw_max)
                                row_data["hw_age_min"] = int(hw_min)
                                row_data["hw_age_max"] = int(hw_max)
                                row_data["MinYearsSinceDist"] = int(min_years)

                            except ValueError:
                                sw_min = 0
                                sw_max = 210
                                hw_min = 0
                                hw_max = 210
                                min_years = -1

                                row_data["sw_age_min"] = int(sw_min)
                                row_data["sw_age_max"] = int(sw_max)
                                row_data["hw_age_min"] = int(hw_min)
                                row_data["hw_age_max"] = int(hw_max)
                                row_data["MinYearsSinceDist"] = int(min_years)

                        if forest_type == "A" and dist == "DISTID4":
                            mask = (
                                (legacy_afforestation_inventory["species"] == species)
                                & (
                                    legacy_afforestation_inventory["yield_class"]
                                    == yield_class
                                )
                                & (legacy_afforestation_inventory["year"] == yr)
                                & (legacy_afforestation_inventory["soil"] == soil)
                            )
                            row_data["Classifier1"] = non_forest_dict[species][soil]
                            try:
                                row_data["Amount"] = legacy_afforestation_inventory.loc[
                                    mask, "area_ha"
                                ].item()

                            except ValueError:
                                row_data["Amount"] = 0

                        elif forest_type == "L" and dist == "DISTID3":
                            mask = (
                                (disturbance_dataframe["Species"] == "?")
                                & (disturbance_dataframe["Yield_class"] == "?")
                                & (
                                    disturbance_dataframe["Year"]
                                    == (forest_baseline_year + yr)
                                )
                                & (disturbance_dataframe["Disturbance_id"] == dist)
                            )

                            try:
                                row_data["Amount"] = disturbance_dataframe.loc[
                                    mask, "Amount"
                                ].item()
                                row_data["MeasureType"] = disturbance_dataframe.loc[
                                    mask, "M_type"
                                ].item()

                            except ValueError:
                                row_data["Amount"] = 0

                        elif (
                            forest_type == "L"
                            and dist != "DISTID4"
                            or dist != "DISTID3"
                        ):
                            mask = (
                                (disturbance_dataframe["Species"] == species)
                                & (disturbance_dataframe["Yield_class"] == yield_class)
                                & (
                                    disturbance_dataframe["Year"]
                                    == (forest_baseline_year + yr)
                                )
                                & (disturbance_dataframe["Disturbance_id"] == dist)
                            )
                            row_data["Classifier1"] = species
                            try:
                                row_data["Amount"] = disturbance_dataframe.loc[
                                    mask, "Amount"
                                ].item()
                                row_data["MeasureType"] = disturbance_dataframe.loc[
                                    mask, "M_type"
                                ].item()

                            except ValueError:
                                row_data["Amount"] = 0

                        else:
                            row_data["Classifier1"] = species
                            row_data["Amount"] = 0

                        data.append(row_data)

        disturbance_df = pd.DataFrame(data)
        disturbance_df = disturbance_df[disturbance_df["Amount"] != 0]

        return disturbance_df

    def fill_baseline_forest(self):
        forest_baseline_year = self.data_manager_class.forest_baseline_year
        classifiers = self.baseline_forest_classifiers

        disturbances = ["DISTID1", "DISTID2"]

        static_cols = self.data_manager_class.static_disturbance_cols

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()

        legacy_years = calibration_year - forest_baseline_year

        yield_name = self.data_manager_class.yield_name_dict

        disturbance_timing = self.loader_class.disturbance_time()

        species_keys = list(classifiers["Species"].keys())
        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        count = 0
        for yr in range(1, (legacy_years + 1)):
            for dist in disturbances:
                for species in species_keys:
                    for forest_type, soil, yield_class in itertools.product(
                        forest_keys, soil_keys, yield_keys
                    ):
                        if (
                            species in yield_name.keys()
                            and yield_class in yield_name[species].keys()
                        ):
                            try:
                                sw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_min",
                                ].item()
                                sw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_max",
                                ].item()
                                hw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_min",
                                ].item()
                                hw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_max",
                                ].item()
                                min_years = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "min years since dist",
                                ].item()
                            except ValueError:
                                sw_min = None
                                sw_max = None
                                hw_min = None
                                hw_max = None
                                min_years = None

                            if (
                                sw_min is not None
                                and sw_max is not None
                                and hw_min is not None
                                and hw_max is not None
                                and min_years is not None
                            ):
                                disturbance_df.at[count, "Classifier1"] = species
                                disturbance_df.at[count, "Classifier2"] = forest_type
                                disturbance_df.at[count, "Classifier3"] = soil
                                disturbance_df.at[count, "Classifier4"] = yield_class

                                disturbance_df.at[count, "UsingID"] = False
                                disturbance_df.at[count, "Year"] = yr
                                disturbance_df.at[count, "DistTypeID"] = dist
                                disturbance_df.at[count, "MeasureType"] = "A"
                                disturbance_df.at[count, "SortType"] = 3
                                disturbance_df.at[count, "Efficiency"] = 1

                                sw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_min",
                                ].item()
                                sw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "sw_age_max",
                                ].item()
                                hw_min = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_min",
                                ].item()
                                hw_max = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "hw_age_max",
                                ].item()
                                min_years = disturbance_timing.loc[
                                    (
                                        (
                                            disturbance_timing.index
                                            == yield_name[species][yield_class]
                                        )
                                        & (disturbance_timing["disturbance_id"] == dist)
                                    ),
                                    "min years since dist",
                                ].item()

                                disturbance_df.at[count, "sw_age_min"] = sw_min
                                disturbance_df.at[count, "sw_age_max"] = sw_max
                                disturbance_df.at[count, "hw_age_min"] = hw_min
                                disturbance_df.at[count, "hw_age_max"] = hw_max
                                disturbance_df.at[
                                    count, "MinYearsSinceDist"
                                ] = min_years

                                disturbance_df.loc[count, static_cols] = -1

                                disturbance_df.loc[count, "Amount"] = 0
                                count += 1

        zero_area_mask = disturbance_df["Amount"] == 0
        disturbance_df.drop(disturbance_df.loc[zero_area_mask].index, inplace=True)

        return disturbance_df

    def fill_scenario_data(self, scenario):
        classifiers = self.scenario_forest_classifiers
        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_df = self.fill_legacy_data(scenario)

        legacy_end_year = disturbance_df.Year.max()

        static_cols = self.data_manager_class.static_disturbance_cols

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(
            range((legacy_end_year + 1), (legacy_end_year + (scenario_years + 1)))
        )

        non_forest_dict = self.data_manager_class.non_forest_dict

        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        disturbances = ["DISTID4"]

        static_defaults = {col: -1 for col in static_cols}

        data = []

        for yr in years:
            for dist in disturbances:
                for species in parser.get_inventory_species(configuration_classifiers):
                    combinations = itertools.product(forest_keys, soil_keys, yield_keys)

                    for combination in combinations:
                        forest_type, soil, yield_class = combination

                        row_data = {
                            "Classifier1": species,
                            "Classifier2": forest_type,
                            "Classifier3": soil,
                            "Classifier4": yield_class,
                            "UsingID": False,
                            "sw_age_min": 0,
                            "sw_age_max": 210,
                            "hw_age_min": 0,
                            "hw_age_max": 210,
                            "MinYearsSinceDist": -1,
                            **static_defaults,
                            "Efficiency": 1,
                            "SortType": 3,
                            "MeasureType": "A",
                            "Amount": 0,
                            "DistTypeID": dist,
                            "Year": yr,
                        }
                        if forest_type == "A":
                            row_data["Classifier1"] = non_forest_dict[species][soil]
                            afforestation_value = afforestation_inventory[species][
                                "mineral"
                            ]

                            if row_data["Classifier3"] == "mineral":
                                try:
                                    row_data["Amount"] = (
                                        afforestation_value
                                        * parser.get_yield_class_proportions(
                                            configuration_classifiers,
                                            species,
                                            yield_class,
                                        )
                                    )
                                except TypeError:
                                    row_data["Amount"] = 0

                            else:
                                row_data["Amount"] = 0
                        else:
                            row_data["Amount"] = 0
                            row_data["Classifier1"] = species

                        data.append(row_data)

        scenario_disturbance_df = pd.DataFrame(data)
        disturbance_df = pd.concat(
            [disturbance_df, scenario_disturbance_df], axis=0, ignore_index=True
        )
        disturbance_df = disturbance_df[disturbance_df["Amount"] != 0]

        return disturbance_df
