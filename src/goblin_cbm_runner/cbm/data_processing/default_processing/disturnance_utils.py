"""
Disturbance Utils
=================

This module contains the DisturbUtils class, which is used to process disturbance data for the CBM model.

"""
import pandas as pd
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import itertools

class DisturbUtils:
    """
    The DisturbUtils class is responsible for processing disturbance data for the CBM model.

    Attributes:
        forest_end_year (int): The final year for simulation, defining the temporal boundary for scenario execution.
        calibration_year (int): The initial year for data calibration.
        data_manager_class (DataManager): Instance of DataManager for managing simulation data and configurations.
        forest_baseline_year (int): The baseline year for forest data.
        baseline_forest_classifiers (dict): Dictionary containing baseline forest classifiers.
        scenario_forest_classifiers (dict): Dictionary containing scenario forest classifiers.
        yield_name_dict (dict): Dictionary containing yield names.

    Parameters:
        config_path (str): Configuration path for setting up CBM simulations.
        calibration_year (int): The initial year for data calibration.
        forest_end_year (int): The final year for simulation, defining the temporal boundary for scenario execution.
        scenario_data (DataFrame): Detailed data of afforestation activities per scenario.

    Methods:
        disturbance_structure():
            Creates a dataframe structure for disturbances.
        _process_scenario_harvest_data(tracker, row_data, context):
            Process the harvest data for a scenario.
        _track_scenario_harvest(tracker, row_data, context):
            Track the harvest scenario in the forest model.
        _drop_zero_area_rows(disturbance_df):
            Drops rows from the disturbance dataframe where the 'Amount' column is zero.
        _get_legacy_classifier_combinations():
            Returns all possible combinations of forest keys, soil keys, and yield keys.
        _get_scenario_classifier_combinations():
            Generates combinations of scenario, forest, soil, and yield classifiers.
        _get_classifier_combinations(species, disturbance=None):
            Generates all possible combinations of forest types, soil classes, and yield classes.
        _get_static_defaults():
            Get the default values for static disturbance columns.
        _generate_row(species, forest_type, soil, yield_class, dist, yr):
            Generates a row of data for a disturbance event.
        _process_scenario_row_data(row_data, context, dataframes):
            Process the row data for a scenario based on the given context and dataframes.
        _process_row_data(row_data, context, dataframes):  
            Process the row data based on the given context and dataframes.
        _handle_legacy_scenario_forest(row_data, context, dataframes):
            Handles the legacy scenario forest by updating the disturbance timing and setting the amount based on the area.
        _handle_scenario_afforestation(row_data, context, dataframes):
            Handle the scenario of afforestation.
        _handle_legacy_afforestation(row_data, context, dataframes):
            Handles legacy afforestation by updating the row data with the appropriate classifier and amount.
        _handle_legacy_forest(row_data, context, dataframes):
            Handles legacy forest data by updating disturbance timing and populating row data with relevant information.
        _update_disturbance_timing(row_data, context, dataframes):
            Retrieve disturbance timing information from the disturbance_timing DataFrame.

    """
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        scenario_data
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
    
        self.data_manager_class = DataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
        )
        self.forest_baseline_year = self.data_manager_class.get_afforestation_baseline()

        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]

        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()

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


    def _process_row_data(self, row_data, context, dataframes):
        """
        Process the row data based on the given context and dataframes.

        Args:
            row_data (dict): The row data to be processed.
            context (dict): The context containing forest type and disturbance information.
            dataframes (dict): The dataframes used for processing.

        Returns:
            None
        """

        legacy_afforestation_end_year = self.calibration_year - self.forest_baseline_year
        forest_type = context["forest_type"]
        dist = context["dist"]
        year = context["year"]

        if forest_type == "A" and dist == "DISTID4" and year < legacy_afforestation_end_year:
            self._handle_legacy_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_forest(row_data, context, dataframes)


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


    def _handle_legacy_afforestation(self, row_data, context, dataframes):
        """
        Handles legacy afforestation by updating the row data with the appropriate classifier and amount.

        Args:
            row_data (dict): The row data to be updated.
            context (dict): The context containing species, yield class, year, and soil information.
            dataframes (dict): A dictionary of dataframes containing the legacy afforestation inventory.

        Returns:
            None
        """
        non_forest_dict = self.data_manager_class.get_non_forest_dict()
        legacy_afforestation_inventory = dataframes["legacy_afforestation_inventory"]
        species = context["species"]
        yield_class = context["yield_class"]
        yr = context["year"]
        soil = context["soil"]

        mask = (
            (legacy_afforestation_inventory["species"] == species)
            & (legacy_afforestation_inventory["yield_class"] == yield_class)
            & (legacy_afforestation_inventory["year"] == yr)
            & (legacy_afforestation_inventory["soil"] == soil)
        )
        row_data["Classifier1"] = non_forest_dict[species][soil]
        try:
            row_data["Amount"] = legacy_afforestation_inventory.loc[mask, "area_ha"].item()
        except ValueError:
            row_data["Amount"] = 0
      

    def _handle_legacy_forest(self, row_data, context, dataframes):
        """
        Handles legacy forest data by updating disturbance timing and populating row data with relevant information.

        Args:
            row_data (dict): The row data to be updated with disturbance information.
            context (dict): The context containing relevant information for the disturbance handling.
            dataframes (dict): A dictionary of dataframes containing disturbance data.

        Returns:
            None
        """
        # ... logic for legacy forest ...
        # This includes your logic for DISTID3, DISTID1, DISTID2, and the else block

        dist = context["dist"]
        disturbance_dataframe = dataframes["disturbance_dataframe"]
        species = context["species"]
        yield_class = context["yield_class"]
        yr = context["year"]
        forest_baseline_year = context["forest_baseline_year"]


        self._update_disturbance_timing(row_data, context, dataframes)

        if dist == "DISTID3":
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
                row_data["SortType"] = disturbance_dataframe.loc[
                    mask, "SortType"
                ].item()
            except ValueError:
                row_data["Amount"] = 0

            


        elif (
                dist == "DISTID1" or dist == "DISTID2"
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
                row_data["SortType"] = disturbance_dataframe.loc[
                    mask, "SortType"
                ].item()
                
            except ValueError:
                row_data["Amount"] = 0

        else:
            row_data["Classifier1"] = species
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