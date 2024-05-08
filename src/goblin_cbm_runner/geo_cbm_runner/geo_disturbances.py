"""
Geo Disturbances Module
=======================
This module manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios
involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes
disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

"""
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.geo_cbm_runner.geo_inventory import Inventory
import pandas as pd
import itertools
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class Disturbances:
    """
    Manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios 
    involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes 
    disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

    Attributes:
        forest_end_year (int): Target end year for forest simulation data.
        calibration_year (int): Base year for data calibration within the simulation.
        loader_class (Loader): Instance responsible for loading external data resources.
        data_manager_class (DataManager): Manages retrieval and organization of simulation data.
        baseline_forest_classifiers (dict): Classifier information for baseline forest scenarios.
        scenario_forest_classifiers (dict): Classifier information for specific simulation scenarios.
        afforestation_data (DataFrame): Contains data on afforestation activities, including species and areas.
        inventory_class (Inventory): Manages the preparation and structuring of forest inventory data.
        disturbance_timing (DataFrame): Contains information on the timing and type of disturbances.
        disturbance_dataframe (DataFrame): Central repository of disturbance event data.
        scenario_disturbance_dict (dict): Holds scenario-specific disturbance information.
        legacy_disturbance_dict (dict): Stores information on disturbances in legacy forests.
        yield_name_dict (dict): Maps yield classes to their corresponding names for easier reference.

    Parameters:
        config_path (str): Path to the configuration file guiding the simulation setup.
        calibration_year (int): Reference year from which simulation data is calibrated.
        forest_end_year (int): Designated end year for the simulation's forest data.
        afforestation_data (DataFrame): Data detailing afforestation projects, including species and area.
        scenario_data (DataFrame): Data defining various simulation scenarios.

    Methods:
        scenario_afforestation_area(scenario):
            Calculates afforestation areas for a given scenario, breaking down by species and yield class.
        
        disturbance_structure():
            Establishes the DataFrame structure for recording disturbance events.
        
        fill_baseline_forest():
            Populates disturbance data for the baseline forest, considering historical disturbances.
        
        fill_scenario_data(scenario):
            Fills in disturbance data for a specified simulation scenario, incorporating scenario-specific events.
        
        _process_scenario_harvest_data(tracker, row_data, context):
            Processes and tracks harvest data for a scenario, updating tracker states based on disturbances.
        
        _track_scenario_harvest(tracker, row_data, context):
            Specifically tracks harvesting activities within a scenario, adjusting forest composition accordingly.
        
        _drop_zero_area_rows(disturbance_df):
            Removes rows with zero area from the disturbance DataFrame to clean up the dataset.
        
        _get_legacy_classifier_combinations():
            Generates combinations of classifiers for legacy forests, aiding in disturbance data generation.
        
        _get_scenario_classifier_combinations():
            Produces classifier combinations for scenario-specific forests, supporting disturbance simulations.
        
        _get_classifier_combinations(species, disturbance):
            Creates all possible combinations of classifiers based on species and disturbance type.
        
        _get_static_defaults():
            Retrieves default values for static columns in the disturbance DataFrame.
        
        _generate_row(species, forest_type, soil, yield_class, dist, yr):
            Generates a single row of disturbance data based on specified parameters.
        
        _process_scenario_row_data(row_data, context, dataframes):
            Processes row data for a given scenario, applying context-specific rules and adjustments.
        
        _handle_legacy_scenario_forest(row_data, context, dataframes):
            Handles disturbance data generation for legacy forests within a scenario.
        
        _handle_scenario_afforestation(row_data, context, dataframes):
            Manages afforestation data within a scenario, adjusting for new forest growth.
        
        _update_disturbance_timing(row_data, context, dataframes):
            Updates the timing for disturbances based on scenario and forest conditions.
        
        get_legacy_forest_area_breakdown():
            Calculates a detailed breakdown of legacy forest areas, considering species, yield classes, and soil types.
        
        legacy_disturbance_tracker(tracker, years):
            Applies legacy disturbances to the forest tracker, updating forest composition over specified years.
    """
    
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        scenario_data
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
        
        self.loader_class = Loader()
        self.data_manager_class = GeoDataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
        )
        self.forest_baseline_year = self.data_manager_class.get_forest_baseline_year()

        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.afforestation_data = afforestation_data
        self.inventory_class = Inventory(
            calibration_year, config_path, scenario_data, afforestation_data
        )

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.disturbance_dataframe = self.loader_class.disturbance_data()
        self.scenario_disturbance_dict = self.data_manager_class.get_scenario_disturbance_dict()
        self.legacy_disturbance_dict = self.data_manager_class.get_legacy_disturbance_dict()
        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()


    def scenario_afforestation_area(self, scenario):
        """
        Calculates the afforestation area for a given scenario.

        Parameters:
            scenario (str): The scenario to calculate afforestation for.

        Returns:
            dict: A dictionary with species as keys and afforestation areas as values.
        """
        scenario_years = self.forest_end_year - self.calibration_year

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        aggregated_data = self.afforestation_data.groupby(['species', 'yield_class', 'scenario'])['total_area'].sum().reset_index()

        for species in parser.get_inventory_species(classifiers):

            species_data = aggregated_data[(aggregated_data['species'] == species) & (aggregated_data['scenario'] == scenario)]
    
            result_dict[species] = {}
                
            for index, row in species_data.iterrows():

                yield_class = row['yield_class']
                total_area = row['total_area']
                
                result_dict[species][yield_class] ={}
                result_dict[species][yield_class]["mineral"] = total_area / scenario_years

        return result_dict


    def disturbance_structure(self):
        """
        Creates a dataframe structure for disturbances.

        Returns:
            DataFrame: A dataframe with the structure for disturbances.
        """
        columns = self.data_manager_class.get_disturbance_cols()
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df


    def fill_baseline_forest(self):
        """
        Fills the baseline (managed) forest with disturbance data.

        Returns:
            pandas.DataFrame: DataFrame containing disturbance data.
        """

        disturbance_df = self.disturbance_structure()

        legacy_years = self.forest_end_year  - self.forest_baseline_year

        years = list(
            range(1, (legacy_years + 1))
        )

        disturbance_timing = self.disturbance_timing 

        data = []

        tracker = AfforestationTracker()

        self.legacy_disturbance_tracker(tracker, years)

        for yr in years:
            for stand in tracker.disturbed_stands:
                if stand.year == yr:
                    
                    row_data = self._generate_row(stand.species, "L", stand.soil, stand.yield_class, stand.dist, yr)

                    context = {"forest_type":"L",
                                "species":stand.species,
                                "yield_class":stand.yield_class,
                                "area":stand.area,
                                "dist":stand.dist,}
                    dataframes = {"disturbance_timing":disturbance_timing}

                    self._process_scenario_row_data(row_data,context, dataframes)

                    data.append(row_data)

        disturbance_df = pd.DataFrame(data)
        disturbance_df = self._drop_zero_area_rows(disturbance_df)

        return disturbance_df


    def fill_scenario_data(self, scenario):
        """
        Fills the disturbance data for a given scenario.

        Args:
            scenario: The scenario for which to fill the disturbance data.

        Returns:
            The disturbance data DataFrame after filling with scenario data.
        """
        
        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_timing = self.disturbance_timing 

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(
            range(1, (scenario_years + 1))
        )

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for yr in years:
            for dist in disturbances:
                if dist == "DISTID4":
                    for species in parser.get_inventory_species(configuration_classifiers):
                        combinations = self._get_scenario_classifier_combinations()

                        for combination in combinations:
                            forest_type, soil, yield_class = combination

                            row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr)

                            context = {"forest_type":forest_type, 
                                        "species":species, 
                                        "soil":soil, 
                                        "yield_class":yield_class, 
                                        "dist":dist, 
                                        "year":yr,
                                        "configuration_classifiers":configuration_classifiers,
                                        "non_forest_dict":non_forest_dict,
                                        "harvest_proportion": self.scenario_disturbance_dict[scenario][species],
                                        "age": 0
                                }

                            dataframes = {"afforestation_inventory":afforestation_inventory}

                            self._process_scenario_row_data(row_data,context, dataframes)

                            self._process_scenario_harvest_data(tracker, row_data, context)

                            data.append(row_data)
            tracker.move_to_next_age()

        for yr in years:
            for stand in tracker.disturbed_stands:
                if stand.year == yr:
                    
                    row_data = self._generate_row(stand.species, "L", stand.soil, stand.yield_class, stand.dist, yr)

                    context = {"forest_type":"L",
                                "species":stand.species,
                                "yield_class":stand.yield_class,
                                "area":stand.area,
                                "dist":stand.dist,}
                    dataframes = {"disturbance_timing":disturbance_timing}

                    self._process_scenario_row_data(row_data,context, dataframes)

                    data.append(row_data)

        scenario_disturbance_df = pd.DataFrame(data)

        scenario_disturbance_df = self._drop_zero_area_rows(scenario_disturbance_df)

        return scenario_disturbance_df


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
           

    def get_legacy_forest_area_breakdown(self):
        """
        Calculate the breakdown of legacy forest area based on species, yield class, soil type, and age.

        Returns:
            pandas.DataFrame: DataFrame containing the breakdown of legacy forest area.
        """
        age_df = self.loader_class.forest_age_structure()
        data_df = self.inventory_class.legacy_forest_inventory()
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
    

    def legacy_disturbance_tracker(self, tracker, years):
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
        data_df = self.get_legacy_forest_area_breakdown()
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
            

