"""
Geo Inventory Module
====================
This module manages and processes forest inventory data for Carbon Budget Modeling (CBM) simulations at the catchment level, 
including handling of legacy forest data and afforestation projects. 
This class is essential for creating accurate and scenario-specific inventory structures that feed into CBM simulations, 
enabling detailed analysis of forest carbon dynamics over time.

"""
import pandas as pd
import os
import itertools
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.geo_cbm_runner.catchment_forest_cover import CatchmentForest


class Inventory:
    """
    Manages and processes forest inventory data for Carbon Budget Modeling (CBM) simulations at the catchment level, 
    including handling of legacy forest data and afforestation projects. This class is essential 
    for creating accurate and scenario-specific inventory structures that feed into CBM simulations, 
    enabling detailed analysis of forest carbon dynamics over time.

    Attributes:
        loader_class (Loader): Utilized for loading external data resources, such as forest age structures.
        data_manager_class (DataManager): Manages data retrieval and configuration, ensuring scenario-specific data is accurately utilized.
        afforestation_data (dict): Contains detailed information on afforestation events, crucial for scenario-based inventory adjustments.
        age_df (DataFrame): A DataFrame detailing forest age structures, pivotal for inventory creation and analysis.
        baseline_forest_classifiers (dict): Holds classifier information for the baseline (legacy) forest scenario, guiding baseline inventory creation.
        scenario_forest_classifiers (dict): Contains classifier information for various simulation scenarios, enabling dynamic inventory structuring.
        legacy_year (int): Specifies the calibration year, serving as a reference point for analyzing legacy forest data.
        soils_dict (dict): A comprehensive dictionary mapping soil types, aiding in the categorization of forest data by soil characteristics.
        yield_baseline_dict (dict): Maps yield classes to their baseline proportions, essential for calculating legacy forest inventory.

    Methods:
        legacy_forest_inventory():
            Retrieves and structures legacy forest inventory data, providing a foundation for baseline scenario simulations.
        
        make_inventory_structure(scenario, path, ID="False", delay=0, UNFCCCLC=2):
            Constructs the inventory data structure for a given scenario, incorporating essential parameters like ID flags, delay years, and land class codes.
        
        fill_baseline_inventory(scenario, inventory_df, forest_type, species, soil, yield_class, ageID):
            Populates the baseline inventory DataFrame with data specific to legacy forests, accounting for forest type, species, soil composition, yield class, and age.
        
        inventory_iterator(scenario, inventory_df):
            Iterates over the inventory DataFrame, filling it with relevant data for each combination of forest type, species, soil, yield class, and age, tailored to the scenario.
        
        afforestation_inventory(scenario, inventory_df):
            Generates inventory data for afforestation activities within a given scenario, ensuring afforested areas are accurately represented in the simulation.
        
        scenario_afforestation_dict(scenario_afforestation_areas):
            Creates a dictionary mapping species and yield classes to afforestation areas, based on scenario-specific afforestation data.
        
        combined_mineral_afforestation_dict(scenario_afforestation_areas):
            Merges afforestation data for mineral soils with legacy afforestation data, providing a comprehensive view of new forest growth.
        
        legacy_afforestation():
            Processes legacy afforestation data, integrating historical afforestation activities into the inventory.
        
        legacy_afforestation_annual():
            Structures annual legacy afforestation data, breaking down historical afforestation by year for detailed analysis.
        
        afforestation_annual_dict(afforestation_df):
            Transforms annual afforestation data into a dictionary format, facilitating easy access and manipulation within simulations.
    """
    def __init__(self, calibration_year, config_path, scenario_data, afforestation_data):
        self.catchment_forest = CatchmentForest()
        self.sc_fetcher = ScenarioDataFetcher(scenario_data)
        self.catchment = self.sc_fetcher.get_catchment_name()  
        self.loader_class = Loader()
        self.data_manager_class = GeoDataManager(calibration_year=calibration_year, config_file=config_path)
        self.afforestation_data = afforestation_data
        self.age_df = self.loader_class.forest_age_structure()
        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.legacy_year = self.data_manager_class.get_forest_baseline_year()
        self.soils_dict = self.data_manager_class.get_soils_dict()
        self.yield_baseline_dict = self.data_manager_class.get_yield_baseline_dict()


    def legacy_forest_inventory(self):
        forest_cover = self.catchment_forest.get_catchment_forest(self.catchment)

        return forest_cover

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
        """
        Fills the baseline inventory dataframe with calculated values based on the given parameters.

        Parameters:
            scenario (str): The scenario for the inventory.
            inventory_df (pandas.DataFrame): The baseline inventory dataframe to be filled.
            forest_type (str): The forest type (L, A).
            species (str): The species of the forest.
            soil (str): The soil type.
            yield_class (str): The yield class.
            ageID (int): The age ID.

        Returns:
            pandas.DataFrame: The filled baseline inventory dataframe.
        """

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

        if species in self.yield_baseline_dict:
            yield_dict = self.yield_baseline_dict[species]
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

                inventory_df.loc[mask, "LastDist"] = "DISTID3"
        else:
            inventory_df.loc[mask, "Area"] = 0.0

        return inventory_df
    

    def inventory_iterator(self, scenario, inventory_df):
        """
        Iterates over different combinations of age, species, forest type, soil class, and yield class
        to fill the baseline inventory dataframe for a given scenario.

        Args:
            scenario (str): The scenario for which the baseline inventory is being filled.
            inventory_df (pandas.DataFrame): The baseline inventory dataframe.

        Returns:
            pandas.DataFrame: The updated baseline inventory dataframe.
        """

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
        """
        Calculate the afforestation inventory based on the given scenario and inventory dataframe.

        Parameters:
            scenario (str): The scenario for which the afforestation inventory is calculated.
            inventory_df (pd.DataFrame): The inventory dataframe containing the classifier information.

        Returns:
            pd.DataFrame: The updated inventory dataframe with afforestation areas calculated.
        """
        classifiers = self.scenario_forest_classifiers

        scenario_afforestation_data = self.afforestation_data

        mask = scenario_afforestation_data["scenario"] == scenario

        afforestation_areas = scenario_afforestation_data.copy(deep=True)

        scenario_afforestation_areas = afforestation_areas.loc[mask]

        mineral_areas_dicts = self.scenario_afforesation_dict(scenario_afforestation_areas)


        non_forest_dict = self.data_manager_class.get_non_forest_dict()

       
        for species in mineral_areas_dicts.keys():
            for yield_class in mineral_areas_dicts[species].keys():
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
                        inventory_df.loc[inventory_mask, "Area"] = mineral_areas_dicts[species][yield_class] * 1e3

        inventory_df["HistDist"] = "DISTID5"

        inventory_df["LastDist"] = "DISTID5"

        return inventory_df


    def scenario_afforesation_dict(self, scenario_afforestation_areas):
        """
        Calculate the areas of afforestation for each yield class and species based on the scenario afforestation areas.

        Args:
            scenario_afforestation_areas (ScenarioAfforestationAreas): An object containing the species and total area of afforestation for each species.

        Returns:
            dict: A dictionary containing the areas of afforestation for each yield class and species.
        """

        areas_dict ={}

        for species, yield_class, total_area in zip(scenario_afforestation_areas.species, scenario_afforestation_areas.yield_class, scenario_afforestation_areas.total_area):
            if species not in areas_dict:
                areas_dict[species] = {}
            if yield_class not in areas_dict[species]:
                areas_dict[species][yield_class] = 0
            areas_dict[species][yield_class] += total_area


        return areas_dict

