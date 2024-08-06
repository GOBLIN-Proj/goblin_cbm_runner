"""
Scenario Inventory Module 
=========================
This module is responsible for managing scenario inventory data for forest simulation in a CBM (Carbon Budget Modeling) context.
It handles the creation and structuring of inventory data for both baseline and scenario-based simulations.
"""
import pandas as pd
import os
import itertools
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager


class SCInventory:
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
        scenario_inventory: Calculate the afforestation inventory based on the given scenario and inventory dataframe.
        scenario_afforesation_dict: Calculate the areas of afforestation for each yield class and species based on the scenario afforestation areas.
    """
    def __init__(self, calibration_year, config_path, afforestation_data):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(calibration_year=calibration_year, config_file=config_path)
        self.afforestation_data = afforestation_data
        self.age_df = self.loader_class.forest_age_structure()
        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]


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


    def scenario_inventory(self, scenario, path):
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

        mineral_areas_dicts = self.scenario_afforesation_dict(scenario)

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        for yield_class in classifiers["Yield classes"].keys():
            if yield_class in mineral_areas_dicts.keys():
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
                            ] = 0.0
                        else:
                            inventory_df.loc[inventory_mask, "Area"] = mineral_areas_dicts[
                                yield_class
                            ][species] 

        inventory_df["HistDist"] = "DISTID5"

        inventory_df["LastDist"] = "DISTID5"

        return inventory_df
    

    def scenario_afforesation_dict(self, scenario):
        """
        Calculate the areas of afforestation for each yield class and species based on the scenario afforestation areas.

        Args:
            scenario_afforestation_areas (ScenarioAfforestationAreas): An object containing the species and total area of afforestation for each species.

        Returns:
            dict: A dictionary containing the areas of afforestation for each yield class and species.
        """
        mask = self.afforestation_data["scenario"] == scenario

        scenario_afforestation_areas = self.afforestation_data.loc[mask]

        areas_dict ={}

        for yield_class, species, total_area in zip(scenario_afforestation_areas.yield_class, scenario_afforestation_areas.species, scenario_afforestation_areas.total_area):
            if yield_class not in areas_dict:
                areas_dict[yield_class] = {}
            if species not in areas_dict[yield_class]:
                areas_dict[yield_class][species] = 0
            areas_dict[yield_class][species] += total_area

        return areas_dict