import pandas as pd
import os
import itertools
import cbm_runner.parser as parser
from cbm_runner.loader import Loader
from cbm_runner.cbm_runner_data_manager import DataManager


class Inventory:
    def __init__(self, calibration_year, config_path, afforestation_data):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(calibration_year, config_path)
        self.afforestation_data = afforestation_data
        self.age_df = self.loader_class.forest_age_structure()
        self.baseline_forest_classifiers = self.data_manager_class.classifiers[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.classifiers[
            "Scenario"
        ]

    def legacy_forest_inventory(self):
        legacy_data = self.loader_class.NIR_forest_data_ha()

        species_proportion = self.loader_class.cso_species_breakdown()

        # legacy_year = self.data_manager_class.forest_baseline_year
        legacy_year = self.data_manager_class.afforestation_baseline

        species = {"Sitka": "conifer", "SGB": "broadleaf"}

        cols = ["species", "peat", "mineral"]

        data = pd.DataFrame(columns=cols)

        for i, key in enumerate(species.keys()):
            data.loc[i, "species"] = key
            data.loc[i, "peat"] = (
                legacy_data.loc[legacy_year, "organic_kha"].item()
                * species_proportion.at[legacy_year, species[key]]
            )
            data.loc[i, "mineral"] = (
                legacy_data.loc[legacy_year, "mineral_kha"].item()
                * species_proportion.at[legacy_year, species[key]]
            )

        return data

    def make_inventory_structure(self, scenario, path, ID="False", delay=0, UNFCCCLC=2):
        age_df = self.age_df

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
            classifiers_path = os.path.join(path, str(scenario), "classifiers.csv")
            forest_keys = self.data_manager_class.forest_type_keys["afforestation"]

        else:
            classifiers = self.baseline_forest_classifiers
            classifiers_path = os.path.join(path, "classifiers.csv")
            forest_keys = self.data_manager_class.forest_type_keys["legacy"]

        yield_name_dict = self.data_manager_class.yield_name_dict
        afforestation_yield_name_dict = (
            self.data_manager_class.afforestation_yield_name_dict
        )
        non_forest_soils = self.data_manager_class.non_forest_soils

        classifiers_df = pd.read_csv(classifiers_path)

        classifiers_df = classifiers_df.loc[(classifiers_df["name"] != "_CLASSIFIER")]

        inventory_classifiers_cols = [
            f"Classifier{x}" for x in classifiers_df["classifier_id"].unique()
        ]

        inventory_static_cols = [
            "UsingID",
            "Age",
            "Area",
            "Delay",
            "UNFCCCLC",
            "HistDist",
            "LastDist",
        ]

        inventory_cols = inventory_classifiers_cols + inventory_static_cols

        inventory_df = pd.DataFrame(columns=inventory_cols)

        species_keys = list(classifiers["Species"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        combinations = itertools.product(
            species_keys, forest_keys, soil_keys, yield_keys
        )

        count = 0

        for species, typ, soil, yc in combinations:
            if typ == "L":
                for yr in age_df["year"]:
                    if species in yield_name_dict:
                        if yc in yield_name_dict[species].keys():
                            inventory_df.loc[count, "Classifier1"] = species
                            inventory_df.loc[count, "Classifier2"] = typ
                            inventory_df.loc[count, "Classifier3"] = soil
                            inventory_df.loc[count, "Classifier4"] = yc
                            inventory_df.loc[count, "Age"] = yr

                            count += 1

            elif typ == "A":
                if species in afforestation_yield_name_dict.keys():
                    if species in non_forest_soils[soil]:
                        if yc in afforestation_yield_name_dict[species]:
                            inventory_df.loc[count, "Classifier1"] = species
                            inventory_df.loc[count, "Classifier2"] = typ
                            inventory_df.loc[count, "Classifier3"] = soil
                            inventory_df.loc[count, "Classifier4"] = yc
                            inventory_df.loc[count, "Age"] = 0

                        count += 1

            inventory_df["Area"] = 0
            inventory_df["UsingID"] = ID
            inventory_df["Delay"] = delay

            inventory_df.loc[(inventory_df["Classifier2"] == "L"), "UNFCCCLC"] = 0
            inventory_df.loc[
                (inventory_df["Classifier2"] == "A"), "UNFCCCLC"
            ] = UNFCCCLC

        return inventory_df

    def fill_baseline_inventory(
        self,
        scenario,
        inventory_df,
        forest_type,
        species,
        soil,
        yield_class,
        ageID,
    ):
        age_df = self.age_df
        data_df = self.legacy_forest_inventory()

        mask = (
            (inventory_df["Classifier1"] == species)
            & (inventory_df["Classifier2"] == forest_type)
            & (inventory_df["Classifier3"] == soil)
            & (inventory_df["Classifier4"] == yield_class)
            & (inventory_df["Age"] == ageID)
        )

        species_exists = species in data_df["species"].unique()

        data_mask = data_df["species"] == species

        age_mask = age_df["year"] == ageID

        if species in self.data_manager_class.yield_basline_dict:
            yield_dict = self.data_manager_class.yield_basline_dict[species]
        else:
            yield_dict = None

        if species_exists and yield_class in yield_dict:
            if forest_type == "L":
                inventory_df.loc[mask, "Area"] = (
                    data_df.loc[data_mask, soil].item()
                    * yield_dict[yield_class]
                    * age_df.loc[age_mask, "aggregate"].item()
                )
                inventory_df.loc[mask, "HistDist"] = "DISTID3"

                inventory_df.loc[mask, "LastDist"] = "DISTID5"
        else:
            inventory_df.loc[mask, "Area"] = 0

        return inventory_df

    def inventory_iterator(self, scenario, inventory_df):
        classifiers = self.baseline_forest_classifiers

        age_df = self.age_df

        # Extract the keys from classifiers
        species_keys = list(classifiers["Species"].keys())
        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        combinations = itertools.product(
            age_df["year"], species_keys, forest_keys, soil_keys, yield_keys
        )

        for AgeID, species, forest, soil, yield_class in combinations:
            inventory_df = self.fill_baseline_inventory(
                scenario,
                inventory_df,
                forest,
                species,
                soil,
                yield_class,
                AgeID,
            )

        inventory_df = inventory_df[inventory_df["Area"] != 0]

        return inventory_df

    def afforestation_inventory(self, scenario, inventory_df):
        classifiers = self.scenario_forest_classifiers

        scenario_afforestation_data = self.afforestation_data

        mask = scenario_afforestation_data["scenario"] == scenario

        afforestation_areas = scenario_afforestation_data.copy(deep=True)

        scenario_afforestation_areas = afforestation_areas.loc[mask]

        mineral_areas_dicts = self.combined_mineral_afforestation_dict(
            scenario_afforestation_areas
        )
        legacy_afforestation_peat_dict = self.legacy_afforestation()[
            "peat_afforestation"
        ]

        non_forest_dict = self.data_manager_class.non_forest_dict

        for yield_class in classifiers["Yield classes"].keys():
            for species in mineral_areas_dicts[yield_class].keys():
                for soil in classifiers["Soil classes"].keys():
                    inventory_mask = (
                        (inventory_df["Classifier1"] == non_forest_dict[species][soil])
                        & (inventory_df["Classifier2"] == "A")
                        & (inventory_df["Classifier3"] == soil)
                        & (inventory_df["Classifier4"] == yield_class)
                    )

                    if soil == "peat":
                        inventory_df.loc[
                            inventory_mask, "Area"
                        ] = legacy_afforestation_peat_dict[yield_class][species]
                    else:
                        inventory_df.loc[inventory_mask, "Area"] = mineral_areas_dicts[
                            yield_class
                        ][species]

        inventory_df["HistDist"] = "DISTID3"

        inventory_df["LastDist"] = "DISTID5"

        return inventory_df

    def scenario_afforesation_dict(self, scenario_afforestation_areas):
        yield_basline_dict = self.data_manager_class.yield_basline_dict

        scenario_areas_dicts = dict(
            zip(
                scenario_afforestation_areas.species,
                scenario_afforestation_areas.total_area,
            )
        )

        areas_dict = {}

        for species in scenario_areas_dicts.keys():
            for yield_class in yield_basline_dict[species].keys():
                if yield_class not in areas_dict:
                    areas_dict[yield_class] = {}

                areas_dict[yield_class][species] = (
                    scenario_areas_dicts[species]
                    * yield_basline_dict[species][yield_class]
                )

        return areas_dict

    def combined_mineral_afforestation_dict(self, scenario_afforestation_areas):
        scenarios_afforesation_dict = self.scenario_afforesation_dict(
            scenario_afforestation_areas
        )
        legacy_afforestation_mineral_dict = self.legacy_afforestation()[
            "mineral_afforestation"
        ]

        areas_dicts = {
            yield_class: {
                species: scenarios_afforesation_dict.get(yield_class, {}).get(
                    species, 0
                )
                + legacy_afforestation_mineral_dict[yield_class][species]
                for species in legacy_afforestation_mineral_dict[yield_class]
            }
            for yield_class in legacy_afforestation_mineral_dict.keys()
        }

        return areas_dicts

    def legacy_afforestation(self):
        legacy_afforestation_data = self.loader_class.afforesation_areas_KB()

        soils_dict = self.data_manager_class.soils_dict
        # legacy_year = self.data_manager_class.forest_baseline_year
        legacy_year = self.data_manager_class.afforestation_baseline

        names_dict = self.data_manager_class.species_name_dict

        index = legacy_afforestation_data.index.unique()

        peat_afforestation = pd.DataFrame()
        mineral_afforestation = pd.DataFrame()

        count = 0
        for year in index:
            if year >= legacy_year:
                for species in legacy_afforestation_data.loc[year, "cohort"].unique():
                    yield_class = list(names_dict[species].keys())

                    peat_afforestation.loc[count, "year"] = int(year)
                    peat_afforestation.loc[count, "yield_class"] = yield_class[0]

                    peat_mask = (
                        (legacy_afforestation_data["soil"].isin(soils_dict["peat"]))
                        & (legacy_afforestation_data["cohort"] == species)
                        & (legacy_afforestation_data.index == year)
                    )

                    peat_afforestation.loc[
                        count, names_dict[species][yield_class[0]]
                    ] = legacy_afforestation_data.loc[peat_mask, "area_ha"].sum()

                    peat_afforestation.fillna(0, inplace=True)

                    mineral_afforestation.loc[count, "year"] = int(year)
                    mineral_afforestation.loc[count, "yield_class"] = yield_class[0]

                    mineral_mask = (
                        (legacy_afforestation_data["soil"].isin(soils_dict["mineral"]))
                        & (legacy_afforestation_data["cohort"] == species)
                        & (legacy_afforestation_data.index == year)
                    )

                    mineral_afforestation.loc[
                        count, names_dict[species][yield_class[0]]
                    ] = legacy_afforestation_data.loc[mineral_mask, "area_ha"].sum()
                    mineral_afforestation.fillna(0, inplace=True)

                    count += 1

        peat_column_sums_dict = {
            yield_class: {
                col: peat_afforestation[
                    peat_afforestation["yield_class"] == yield_class
                ][col].sum()
                for col in peat_afforestation.columns[2:]
            }
            for yield_class in peat_afforestation["yield_class"].unique()
        }

        mineral_column_sums_dict = {
            yield_class: {
                col: mineral_afforestation[
                    mineral_afforestation["yield_class"] == yield_class
                ][col].sum()
                for col in mineral_afforestation.columns[2:]
            }
            for yield_class in mineral_afforestation["yield_class"].unique()
        }

        return {
            "peat_afforestation": peat_column_sums_dict,
            "mineral_afforestation": mineral_column_sums_dict,
        }

    def legacy_afforestation_annual(self):
        legacy_afforestation_data = self.loader_class.afforesation_areas_KB()
        soils_dict = self.data_manager_class.soils_dict
        # legacy_year = self.data_manager_class.forest_baseline_year
        legacy_year = self.data_manager_class.afforestation_baseline

        names_dict = self.data_manager_class.species_name_dict

        index = legacy_afforestation_data.index.unique()

        peat_afforestation = pd.DataFrame()
        mineral_afforestation = pd.DataFrame()

        count = 0
        for year in index:
            if year >= legacy_year:
                for species in legacy_afforestation_data.loc[year, "cohort"].unique():
                    yield_class = list(names_dict[species].keys())

                    peat_afforestation.loc[count, "year"] = int(year)
                    peat_afforestation.loc[count, "yield_class"] = yield_class[0]

                    peat_mask = (
                        (legacy_afforestation_data["soil"].isin(soils_dict["peat"]))
                        & (legacy_afforestation_data["cohort"] == species)
                        & (legacy_afforestation_data.index == year)
                    )

                    peat_afforestation.loc[
                        count, names_dict[species][yield_class[0]]
                    ] = legacy_afforestation_data.loc[peat_mask, "area_ha"].sum()
                    peat_afforestation.fillna(0, inplace=True)

                    mineral_afforestation.loc[count, "year"] = int(year)
                    mineral_afforestation.loc[count, "yield_class"] = yield_class[0]

                    mineral_mask = (
                        (legacy_afforestation_data["soil"].isin(soils_dict["mineral"]))
                        & (legacy_afforestation_data["cohort"] == species)
                        & (legacy_afforestation_data.index == year)
                    )

                    mineral_afforestation.loc[
                        count, names_dict[species][yield_class[0]]
                    ] = legacy_afforestation_data.loc[mineral_mask, "area_ha"].sum()
                    mineral_afforestation.fillna(0, inplace=True)

                    count += 1

        mineral_afforestation = self.afforestation_annual_dict(mineral_afforestation)
        peat_afforestation = self.afforestation_annual_dict(peat_afforestation)

        return {
            "peat_afforestation": peat_afforestation,
            "mineral_afforestation": mineral_afforestation,
        }

    def afforestation_annual_dict(self, afforestation_df):
        result_dict = {}
        grouped = afforestation_df.groupby("year")

        for year, group in grouped:
            result_dict[year] = {}

            for species in afforestation_df.columns[2:]:
                result_dict[year][species] = {}

                for yield_class in group["yield_class"].unique():
                    mask = (group["yield_class"] == yield_class) & group[
                        species
                    ].notna()

                    result_dict[year][species][yield_class] = group.loc[
                        mask, species
                    ].sum()

        return result_dict
