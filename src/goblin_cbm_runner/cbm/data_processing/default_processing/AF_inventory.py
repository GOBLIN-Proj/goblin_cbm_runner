"""
Afforesation Inventory Module 
==============================
This module is responsible for managing historic afforestation inventory data for forest simulation in a CBM (Carbon Budget Modeling) context.
It handles the creation and structuring of inventory data for both baseline and scenario-based simulations.
"""
import pandas as pd
import os
import itertools
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager


class AFInventory:
    """
    Manages the inventory data for forest simulation in a CBM (Carbon Budget Modeling) context.

    This class is responsible for managing and processing inventory data, including legacy forest inventory and afforestation data. It handles the creation and structuring of inventory data for both baseline and scenario-based simulations.

    Attributes:
        loader_class (Loader): Instance of the Loader class for loading various data.
        data_manager_class (DataManager): Instance of the DataManager class for managing configuration and data retrieval.
        afforestation_data (dict): Data related to afforestation events.
        age_df (DataFrame): Data structure containing information about forest age.
        baseline_forest_classifiers (dict): Classifiers for the baseline forest scenario.
        scenario_forest_classifiers (dict): Classifiers for different scenario-based forests.
        legacy_year (int): The calibration year.
        soils_dict (dict): Dictionary containing information about different soil types.
        yield_baseline_dict (dict): Dictionary mapping yield classes to their respective baseline proportions nationally.

    Methods:
        make_inventory_structure: Creates an inventory structure based on the given scenario and parameters.
        afforestation_inventory: Calculate the afforestation inventory based on the given scenario and inventory dataframe.
        legacy_afforestation: Calculate the afforestation areas for legacy years.
        legacy_afforestation_annual: Calculate the annual afforestation for legacy years.
        afforestation_annual_dict: Generate a dictionary containing annual afforestation data.
    
    """
    def __init__(self, calibration_year, config_path):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(calibration_year=calibration_year, config_file=config_path)
        self.age_df = self.loader_class.forest_age_structure()
        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.legacy_year = self.data_manager_class.get_afforestation_baseline()
        self.soils_dict = self.data_manager_class.get_soils_dict()
        self.yield_baseline_dict = self.data_manager_class.get_yield_baseline_dict()


    def make_inventory_structure(self, scenario, path, ID="False", delay=0, UNFCCCLC=2):
        """
        Creates an inventory structure based on the given scenario and parameters.

        Args:
            scenario (str): The scenario for which the inventory is being created.
            path (str): The path where the inventory will be saved.
            ID (str, optional): Fills the UsingID column, defaults to False.
            delay (int, optional): The delay in years for the inventory. Defaults to 0.
            UNFCCCLC (int, optional): The UNFCCC land class code for the inventory. Defaults to 2.

        Returns:
            pandas.DataFrame: The inventory structure as a DataFrame.
        """
        age_df = self.age_df

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
            classifiers_path = os.path.join(path, str(scenario), "classifiers.csv")
            forest_keys = self.data_manager_class.get_forest_type_keys()["afforestation"]

        else:
            classifiers = self.baseline_forest_classifiers
            classifiers_path = os.path.join(path, "classifiers.csv")
            forest_keys = self.data_manager_class.get_forest_type_keys()["legacy"]

        yield_name_dict = self.data_manager_class.get_yield_name_dict()
        afforestation_yield_name_dict = (
            self.data_manager_class.get_afforestation_yield_name_dict()
        )
        non_forest_soils = self.data_manager_class.get_non_forest_soils()

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

            inventory_df["Area"] = 0.0
            inventory_df["UsingID"] = ID
            inventory_df["Delay"] = delay

            inventory_df.loc[(inventory_df["Classifier2"] == "L"), "UNFCCCLC"] = 0
            inventory_df.loc[
                (inventory_df["Classifier2"] == "A"), "UNFCCCLC"
            ] = UNFCCCLC

        return inventory_df


    def afforestation_inventory(self, scenario, path):
        """
        Calculate the afforestation inventory based on the given scenario and inventory dataframe.

        Parameters:
            scenario (str): The scenario for which the afforestation inventory is calculated.
            inventory_df (pd.DataFrame): The inventory dataframe containing the classifier information.

        Returns:
            pd.DataFrame: The updated inventory dataframe with afforestation areas calculated.
        """
        inventory_df = self.make_inventory_structure(scenario, path)

        classifiers = self.scenario_forest_classifiers

        mineral_areas_dicts = self.legacy_afforestation()["mineral_afforestation"]
        legacy_afforestation_peat_dict = self.legacy_afforestation()["peat_afforestation"]

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

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

        inventory_df["HistDist"] = "DISTID5"

        inventory_df["LastDist"] = "DISTID5"

        return inventory_df
    
    

    def legacy_afforestation(self):
        """
        Calculate the afforestation areas for legacy years.

        Returns a dictionary containing the sum of afforestation areas for peat and mineral soils,
        grouped by yield class.

        Returns:
            dict: A dictionary with the following structure:
                {
                    "peat_afforestation": {
                        yield_class: {
                            col1: sum1,
                            col2: sum2,
                            ...
                        },
                        ...
                    },
                    "mineral_afforestation": {
                        yield_class: {
                            col1: sum1,
                            col2: sum2,
                            ...
                        },
                        ...
                    }
                }
        """
        legacy_afforestation_data = self.loader_class.afforestation_areas_KB()

        soils_dict = self.soils_dict
        legacy_year = self.legacy_year

        names_dict = self.data_manager_class.get_species_name_dict()

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
        """
        Calculate the annual afforestation for legacy years.

        Returns:
            dict: A dictionary containing the annual afforestation data for peat and mineral soils.
                The dictionary has the following keys:
                - "peat_afforestation": A DataFrame containing the annual afforestation data for peat soils.
                - "mineral_afforestation": A DataFrame containing the annual afforestation data for mineral soils.
        """
        legacy_afforestation_data = self.loader_class.afforestation_areas_KB()
        soils_dict = self.soils_dict
        legacy_year = self.legacy_year

        names_dict = self.data_manager_class.get_species_name_dict()

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
        """
        Generate a dictionary containing annual afforestation data.

        Args:
            afforestation_df (pandas.DataFrame): DataFrame containing afforestation data.

        Returns:
            dict: A dictionary with the following structure:
                {
                    year1: {
                        species1: {
                            yield_class1: total1,
                            yield_class2: total2,
                            ...
                        },
                        species2: {
                            yield_class1: total1,
                            yield_class2: total2,
                            ...
                        },
                        ...
                    },
                    year2: {
                        ...
                    },
                    ...
                }
            The dictionary contains the sum of afforestation values for each species and yield class
            for each year in the input DataFrame.
        """
        result_dict = {}
        grouped = afforestation_df.groupby("year")

        for year, group in grouped:
            result_dict[year] = {}

            for species in afforestation_df.columns[2:]:
                result_dict[year][species] = {}

                for yield_class in group["yield_class"].unique():
                    mask = (group["yield_class"] == yield_class) & group[species].notna()

                    result_dict[year][species][yield_class] = group.loc[mask, species].sum()

        return result_dict
