"""
Geo Disturbance Utils
=====================

This module contains the GeoDisturbUtils class, which is used to process disturbance data for the CBM model.
It provides methods to create disturbance data structures, process scenario harvest data, drop zero area rows,
generate classifier combinations, handle afforestation scenarios, and update disturbance timing.

Classes:
    GeoDisturbUtils: A utility class for processing disturbance data.

Methods:
    disturbance_structure: Creates a dataframe structure for disturbances.
    _process_scenario_harvest_data: Processes the harvest data for a scenario.
    _drop_zero_area_rows: Drops rows from the disturbance dataframe where the 'Amount' column is zero.
    _get_legacy_classifier_combinations: Returns all possible combinations of forest keys, soil keys, and yield keys.
    _get_scenario_classifier_combinations: Generates combinations of scenario, forest, soil, and yield classifiers.
    _get_classifier_combinations: Generates all possible combinations of forest types, soil classes, and yield classes.
    _get_static_defaults: Gets the default values for static disturbance columns.
    _generate_row: Generates a row of data for a disturbance event.
    _process_scenario_row_data: Processes the row data for a scenario based on the given context and dataframes.
    _handle_legacy_scenario_forest: Handles the legacy scenario forest by updating the disturbance timing and setting the amount based on the area.
    _handle_scenario_afforestation: Handles the scenario of afforestation.
    _update_disturbance_timing: Retrieves disturbance timing information from the disturbance_timing DataFrame.
    get_legacy_forest_area_breakdown: Calculates the breakdown of legacy forest area based on species, yield class, soil type, and age.
    legacy_disturbance_tracker: Applies legacy disturbances to the forest and returns a disturbance dataframe.
    update_disturbance_row: Updates a single row with the correct disturbance timing information.
    format_disturbance_data: Formats the tracked disturbance data dynamically, ensuring all required columns exist and retrieving timing constraints from `disturbance_timing`.
"""

import pandas as pd
from goblin_cbm_runner.resource_manager.loader import Loader
import itertools

class GeoDisturbUtils:
    def __init__(
        self,
        geo_data_manager
    ):
        self.data_manager_class = geo_data_manager
        self.forest_end_year = self.data_manager_class.get_forest_end_year()
        self.calibration_year = self.data_manager_class.get_calibration_year()

        self.loader_class = Loader()

        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.transition_dict_species = self.data_manager_class.get_transition_dict_species_to_yield()
        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()

        self.sort_dict = self.data_manager_class.get_sort_dict()

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
        Processes the harvest data for a scenario.

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
        
        Returns:
            combinations (generator): A generator that yields all possible combinations of forest keys, soil keys, and yield keys.
        """
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["L"]
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_scenario_classifier_combinations(self, species):
        """
        Generates combinations of scenario, forest, soil, and yield classifiers.

        Args:
            species (str): The species of the forest.

        Returns:
            generator: A generator that yields combinations of scenario, forest, soil, and yield classifiers.
        """
        classifiers = self.scenario_forest_classifiers
        
        forest_keys = ["A"]
        soil_keys = ["mineral"]
        yield_keys = self.transition_dict_species.get(species, [])
        
        return itertools.product(forest_keys, soil_keys, yield_keys)


    def _get_classifier_combinations(self, species, disturbance=None):
        """
        Generates all possible combinations of forest types, soil classes, and yield classes.

        Args:
            species (str): The species of the forest.
            disturbance (str, optional): The disturbance type ID.

        Returns:
            generator: A generator that yields tuples representing the combinations of forest types, soil classes, and yield classes.
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
        Gets the default values for static disturbance columns.

        Returns:
            dict: A dictionary containing the default values for each static disturbance column.
        """
        static_cols = self.data_manager_class.get_static_disturbance_cols()
        return {col: -1 for col in static_cols}


    def _generate_row(self, species, forest_type, soil, yield_class, dist, yr, amount=0):
        """
        Generates a row of data for a disturbance event.

        Args:
            species (str): The species of the forest.
            forest_type (str): The type of forest.
            soil (str): The type of soil.
            yield_class (str): The yield class of the forest.
            dist (int): The disturbance type ID.
            yr (int): The year of the disturbance event.
            amount (float, optional): The amount of disturbance. Defaults to 0.

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
            "SortType": self.sort_dict.get(species, 3),
            "MeasureType": "A",
            "Amount": amount if amount is not None else 0,
            "DistTypeID": dist,
            "Year": yr,
        }
        return row_data


    def _process_scenario_row_data(self, row_data, context, dataframes):
        """
        Processes the row data for a scenario based on the given context and dataframes.

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
        Handles the scenario of afforestation.

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
        """
        Retrieves disturbance timing information from the disturbance_timing DataFrame.

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
        Calculates the breakdown of legacy forest area based on species, yield class, soil type, and age.

        Args:
            inventory_class (str): The forest inventory class.

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


    def legacy_disturbance_tracker(self, inventory_class, year):
        """
        Applies legacy disturbances to the forest and returns a disturbance dataframe.

        Args:
            inventory_class (str): The forest inventory class.
            year (int): The year to apply disturbances.

        Returns:
            pd.DataFrame: A dataframe containing disturbance events.
        """
        data_df = self.get_legacy_forest_area_breakdown(inventory_class)

        disturbance_records = []  # Store disturbance records here

        for i in data_df.index:
            species = data_df.at[i, "species"]
            yield_class = data_df.at[i, "yield_class"]
            soil = data_df.at[i, "soil"]
            area = data_df.at[i, "area"]
            age = data_df.at[i, "age"]

            # Create a disturbance record
            disturbance_record = {
                "Classifier1": species,        # Species
                "Classifier2": "L",           # Assuming "L" is always used here
                "Classifier3": soil,          # Soil type
                "Classifier4": yield_class,   # Yield class
                "Amount": area,     # Disturbed area
                "Year": year,                  # Year of disturbance
                "StandAge": age                # Stand age
            }
            disturbance_records.append(disturbance_record)

        # Convert the list of records into a DataFrame
        disturbance_df = pd.DataFrame(disturbance_records)

        # Return the dataframe with all disturbance events
        return disturbance_df


    def update_disturbance_row(self, row, disturbance_timing_df):
        """
        Updates a single row with the correct disturbance timing information.

        Args:
            row (pandas.Series): A single row from the disturbance DataFrame.
            disturbance_timing_df (pandas.DataFrame): The disturbance timing reference.

        Returns:
            pandas.Series: The updated row.
        """
        row_dict = row.to_dict()  # Convert Series to Dictionary

        self._update_disturbance_timing(row_dict, 
                                        {"species": row_dict["Classifier1"], 
                                        "yield_class": row_dict["Classifier4"], 
                                        "dist": row_dict["DistTypeID"]}, 
                                        {"disturbance_timing": disturbance_timing_df})
        
        return pd.Series(row_dict)  # Convert Dict Back to Series


    def format_disturbance_data(self, disturbance_df, disturbance_timing_df):
        """
        Formats the tracked disturbance data dynamically, ensuring all required columns exist 
        and retrieving timing constraints from `disturbance_timing`.

        Args:
            disturbance_df (pandas.DataFrame): The raw disturbance data.
            disturbance_timing_df (pandas.DataFrame): The disturbance timing reference.

        Returns:
            pandas.DataFrame: A formatted disturbance dataframe with correct age constraints.
        """
        disturbance_dataframe = disturbance_df.copy()

        # Get required column structure
        required_columns = self.disturbance_structure().columns

        # Populate fields based on existing data
        formatted_df = pd.DataFrame(columns=required_columns, index=range(len(disturbance_dataframe)))

        formatted_df["Classifier1"] = disturbance_dataframe["Classifier1"] 
        formatted_df["Classifier2"] = disturbance_dataframe["Classifier2"]
        formatted_df["Classifier3"] = disturbance_dataframe["Classifier3"]
        formatted_df["Classifier4"] = disturbance_dataframe["Classifier4"]
        formatted_df["DistTypeID"] = disturbance_dataframe["DistTypeID"]
        formatted_df["Amount"] = disturbance_dataframe["Amount"]
        formatted_df["Year"] = disturbance_dataframe["Year"]

        # Apply `_generate_row()` correctly
        def generate_row(row):
            return pd.Series(self._generate_row(row["Classifier1"], row["Classifier2"], row["Classifier3"], 
                                                row["Classifier4"], row["DistTypeID"], row["Year"],  row["Amount"]))

        formatted_df = formatted_df.apply(generate_row, axis=1)

        # Apply `_update_disturbance_timing()` correctly
        def update_timing(row):
            row_dict = row.to_dict()  # Convert row to dictionary
            self._update_disturbance_timing(
                row_dict, 
                {"species": row_dict["Classifier1"], "yield_class": row_dict["Classifier4"], "dist": row_dict["DistTypeID"]},
                {"disturbance_timing": disturbance_timing_df}
            )
            return pd.Series(row_dict)  # Convert dictionary back to Series

        formatted_df = formatted_df.apply(update_timing, axis=1)

        # Ensure column order matches `disturbance_structure()`
        formatted_df = formatted_df[required_columns]

        return formatted_df