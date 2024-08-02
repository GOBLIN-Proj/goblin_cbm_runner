"""
Geo Disturbance Utils
=====================

This module contains the GeoDisturbUtils class, which is used to process disturbance data for the CBM model.

"""
import pandas as pd
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.resource_manager.loader import Loader
import itertools

class GeoDisturbUtils:
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        scenario_data
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year

        self.loader_class = Loader()

        self.data_manager_class = GeoDataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
        )

        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]

        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()
        self.legacy_disturbance_dict = self.data_manager_class.get_legacy_disturbance_dict()

    def disturbance_structure(self):
        """
        Creates a dataframe structure for disturbances.

        Returns:
            DataFrame: A dataframe with the structure for disturbances.
        """
        columns = self.data_manager_class.get_disturbance_cols()
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df
    

    def _process_scenario_harvest_data(self, tracker, row_data, context):
        """
        Process the harvest data for a scenario.

        Args:
            tracker (Tracker): The tracker object used to track forest changes.
            row_data (dict): The data for a single row.
            context (dict): The context containing additional information.

        Returns:
            None
        """
        dist = context["dist"]
        area = row_data["Amount"]
        if dist == "DISTID4" and area != 0:
            self._track_scenario_harvest(tracker, row_data, context)
    

    def _track_scenario_harvest(self, tracker, row_data, context):
        """
        Track the harvest scenario in the forest model.

        Args:
            tracker (Tracker): The tracker object used to track forest changes.
            row_data (dict): The data for the current row.
            context (dict): The context containing species, yield class, soil, year, harvest proportion, and age.

        Returns:
            None
        """
        area = row_data["Amount"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        time = context["year"]
        factor = context["harvest_proportion"]
        age = context["age"]

        tracker.afforest(area, species, yield_class, soil, age)
        tracker.forest_disturbance(time, species, yield_class, soil, factor)


    def _drop_zero_area_rows(self, disturbance_df):
        """
        Drops rows from the disturbance dataframe where the 'Amount' column is zero.
        
        Parameters:
            disturbance_df (pandas.DataFrame): The disturbance dataframe.
        
        Returns:
            pandas.DataFrame: The disturbance dataframe with zero area rows dropped.
        """
        disturbance_df = disturbance_df[disturbance_df["Amount"] != 0]
        disturbance_df = disturbance_df.reset_index(drop=True)
        disturbance_df = disturbance_df.sort_values(by=["Year"], ascending=True)
        return disturbance_df


    def _get_legacy_classifier_combinations(self):
        """
        Returns all possible combinations of forest keys, soil keys, and yield keys.
        
        Parameters:
            self (Disturbances): The Disturbances object.
        
        Returns:
            combinations (generator): A generator that yields all possible combinations of forest keys, soil keys, and yield keys.
        """
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["L"]
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_scenario_classifier_combinations(self):
        """
        Generates combinations of scenario, forest, soil, and yield classifiers.

        Returns:
            A generator that yields combinations of scenario, forest, soil, and yield classifiers.
        """
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["A"]
        soil_keys = ["mineral"]
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)


    def _get_classifier_combinations(self, species, disturbance=None):
        """
        Generates all possible combinations of forest types, soil classes, and yield classes.

        Returns:
            A generator that yields tuples representing the combinations of forest types, soil classes, and yield classes.
        """

        classifiers = self.scenario_forest_classifiers

        if disturbance == "DISTID1" or disturbance == "DISTID2":
            forest_keys = ["L"]
            soil_keys = ["?"]
            yield_keys = list(self.yield_name_dict[species].keys())
            return itertools.product(forest_keys, soil_keys, yield_keys)
        else:
            forest_keys = list(classifiers["Forest type"].keys())
            soil_keys = list(classifiers["Soil classes"].keys())
            yield_keys = list(self.yield_name_dict[species].keys())
            return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_static_defaults(self):
        """
        Get the default values for static disturbance columns.

        Returns:
            dict: A dictionary containing the default values for each static disturbance column.
        """
        static_cols = self.data_manager_class.get_static_disturbance_cols()
        return {col: -1 for col in static_cols}


    def _generate_row(self, species, forest_type, soil, yield_class, dist, yr):
        """
        Generates a row of data for a disturbance event.

        Args:
            species (str): The species of the forest.
            forest_type (str): The type of forest.
            soil (str): The type of soil.
            yield_class (str): The yield class of the forest.
            dist (int): The disturbance type ID.
            yr (int): The year of the disturbance event.

        Returns:
            dict: A dictionary containing the row data for the disturbance event.
        """
        static_defaults = self._get_static_defaults()
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
        return row_data


    def _process_scenario_row_data(self, row_data, context, dataframes):
        """
        Process the row data for a scenario based on the given context and dataframes.

        Args:
            row_data (dict): The row data for the scenario.
            context (dict): The context containing forest type and disturbance information.
            dataframes (dict): The dataframes containing relevant data.

        Returns:
            None
        """
        forest_type = context["forest_type"]
        dist = context["dist"]

        if forest_type == "A" and dist == "DISTID4":
            self._handle_scenario_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_scenario_forest(row_data, context, dataframes)



    def _handle_legacy_scenario_forest(self, row_data, context, dataframes):
        """
        Handles the legacy scenario forest by updating the disturbance timing and setting the amount based on the area.

        Args:
            row_data (dict): The row data for the disturbance.
            context (dict): The context information for the disturbance.
            dataframes (dict): The dataframes containing additional data.

        Returns:
            None
        """
        if context["dist"] == "DISTID4":
            row_data["Amount"] = 0
        else:
            self._update_disturbance_timing(row_data, context, dataframes)
            area = context["area"]

            row_data["Amount"] = area


    def _handle_scenario_afforestation(self, row_data, context, dataframes):
        """
        Handle the scenario of afforestation.

        This method calculates the amount of afforestation based on the given row data, context, and dataframes.
        It retrieves the afforestation inventory, non-forest dictionary, species, yield class, soil, and configuration classifiers from the context and dataframes.
        The amount of afforestation is calculated based on the afforestation value, yield class proportions, and classifier3 value.
        If the classifier3 value matches the soil value, the amount is calculated using the afforestation value and yield class proportions.
        If there is a TypeError during the calculation, the amount is set to 0.
        If the classifier3 value does not match the soil value, the amount is set to 0.

        Parameters:
        - row_data (dict): The row data for the afforestation scenario.
        - context (dict): The context containing additional information for the calculation.
        - dataframes (dict): The dataframes containing the afforestation inventory.

        Returns:
        - None
        """
        afforestation_inventory = dataframes["afforestation_inventory"]
        non_forest_dict = context["non_forest_dict"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        #configuration_classifiers = context["configuration_classifiers"]

        # Safely get the value for species and soil, with a default of an empty dictionary
        species_dict = non_forest_dict.get(species, {})

        row_data["Classifier1"] = species_dict.get(soil, "Species not found")

        if row_data["Classifier3"] == soil:
            try:
                # Navigate through the nested dictionaries safely with .get
                species_inventory = afforestation_inventory.get(species, {})
                yield_class_dict = species_inventory.get(yield_class, {})
                afforestation_value = yield_class_dict.get(soil, 0)  # Default to 0 if soil key is not found

                row_data["Amount"] = afforestation_value

            except TypeError:
                row_data["Amount"] = 0
        else:
            row_data["Amount"] = 0

    
    def _update_disturbance_timing(self, row_data, context, dataframes):
        """Retrieve disturbance timing information from the disturbance_timing DataFrame.

        Args:
            row_data (dict): The dictionary containing row data.
            context (dict): The dictionary containing context information.
            dataframes (dict): The dictionary containing dataframes.

        Returns:
            None

        Raises:
            ValueError: If any of the operations fail due to invalid values.
            KeyError: If any of the required keys are not found.

        """
        yield_name = self.yield_name_dict
        species = context["species"]
        yield_class = context["yield_class"]
        dist = context["dist"]
        disturbance_timing = dataframes["disturbance_timing"]

        try:
            timing_info = disturbance_timing.loc[
                (disturbance_timing.index == yield_name[species][yield_class])
                & (disturbance_timing["disturbance_id"] == dist)
            ]
           
            row_data['sw_age_min'] = int(timing_info['sw_age_min'].item())
            row_data['sw_age_max'] = int(timing_info['sw_age_max'].item())
            row_data['hw_age_min'] = int(timing_info['hw_age_min'].item())
            row_data['hw_age_max'] = int(timing_info['hw_age_max'].item())
            row_data['MinYearsSinceDist'] = int(timing_info['min years since dist'].item())
          
        except (ValueError, KeyError):
            # Default values if any of the above operations fail
            
            row_data['sw_age_min'] = 0
            row_data['sw_age_max'] = 210
            row_data['hw_age_min'] = 0
            row_data['hw_age_max'] = 210
            row_data['MinYearsSinceDist'] = -1


    def get_legacy_forest_area_breakdown(self, inventory_class):
        """
        Calculate the breakdown of legacy forest area based on species, yield class, soil type, and age.

        Returns:
            pandas.DataFrame: DataFrame containing the breakdown of legacy forest area.
        """
        age_df = self.loader_class.forest_age_structure()
        data_df = inventory_class.legacy_forest_inventory()
        yield_dict = self.data_manager_class.get_yield_baseline_dict()

        data = []
        for species in data_df["species"].unique():
            for soil in ["mineral", "peat"]:
                for yc in yield_dict[species].keys():
                    for age in age_df["year"].unique():

                        data_mask = data_df["species"] == species
                        age_mask = age_df["year"] == age

                        row_data = {
                            "species": species,
                            "yield_class": yc,
                            "soil": soil,
                            "age": age,
                            "area": data_df.loc[data_mask, soil].item() * yield_dict[species][yc] * age_df.loc[age_mask, "aggregate"].item()
                        }
                        data.append(row_data)

        return pd.DataFrame(data)


    def legacy_disturbance_tracker(self, inventory_class, tracker, years):
        """
        Apply legacy disturbances to the forest tracker.

        Args:
            tracker (object): The forest tracker object.
            years (list): List of years to apply disturbances.

        Returns:
            None

        Note:
            Unlike the default runner, broadleaf disturnbance can be set. 
        """
        data_df = self.get_legacy_forest_area_breakdown(inventory_class)
        yield_name_dict = self.yield_name_dict

        for i in data_df.index:
            species = data_df.at[i, "species"]
            yield_class = data_df.at[i, "yield_class"]
            soil = data_df.at[i, "soil"]
            area = data_df.at[i, "area"]
            age = data_df.at[i, "age"]

            tracker.afforest(area, species, yield_class, soil, age)

        for year in years:
            for species in data_df["species"].unique():
                for soil in data_df["soil"].unique():
                    for yc in yield_name_dict[species].keys():
                        if species == "SGB":
                            dist = self.legacy_disturbance_dict["broadleaf"]
                        else:
                            dist = self.legacy_disturbance_dict["conifer"]

                        tracker.forest_disturbance(year, species, yc, soil, dist)
            tracker.move_to_next_age()