""""
Forest Sim Disturbances
=======================
The ForestSimDistrubances class represents the disturbances in a forest simulation.
This is used when the user wishes to siumulate afforestation with areas per year explicitly defined.
"""

from goblin_cbm_runner.default_runner.disturbances import Disturbances
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.forest_sim.forestsim_inventory import ForSimInventory
import pandas as pd
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class ForestSimDistrubances:
    """
    ForestSimDistrubances class represents the disturbances in a forest simulation.
    This is used when the user wishes to siumulate afforestation with areas per year explicitly defined.
    It provides methods to handle legacy disturbances, scenario disturbances, and afforestation data.

    Attributes:
        config_path (str): The path to the configuration file.
        calibration_year (int): The year used for calibration.
        forest_end_year (int): The year when the forest simulation ends.
        afforestation_data (pd.DataFrame): The data for afforestation.
        afforesataion_annual_data (pd.DataFrame): The annual data for afforestation.
        scenario_data (dict): The scenario data.

    Methods:
        _scenario_afforestation_area(scenario): Calculates the afforestation area for a given scenario.
        legacy_disturbance_afforestation_area(years): Calculates the afforestation area for legacy disturbances in the given years.
        disturbance_structure(): Returns the disturbance structure.
        fill_legacy_data(): Fills the legacy disturbance data.
        fill_baseline_forest(): Fills the baseline forest data.
        fill_scenario_data(scenario): Fills the scenario data for a given scenario.
        _process_scenario_harvest_data(tracker, row_data, context): Processes the scenario harvest data.
        _track_scenario_harvest(tracker, row_data, context): Tracks the scenario harvest.
        _drop_zero_area_rows(disturbance_df): Drops rows with zero area from the disturbance dataframe.
        _get_legacy_classifier_combinations(): Returns the combinations of legacy classifiers.
        _get_scenario_classifier_combinations(): Returns the combinations of scenario classifiers.
        _get_classifier_combinations(): Returns the combinations of classifiers.
        _get_static_defaults(): Returns the static defaults.
        _generate_row(species, forest_type, soil, yield_class, dist, yr): Generates a row of disturbance data.
        _process_scenario_row_data(row_data, context, dataframes): Processes the scenario row data.
        _process_row_data(row_data, context, dataframes): Processes the row data.
        _handle_legacy_scenario_forest(row_data, context, dataframes): Handles the legacy scenario forest.
        _handle_scenario_afforestation(row_data, context, dataframes): Handles the scenario afforestation.
        _handle_legacy_afforestation(row_data, context, dataframes): Handles the legacy afforestation.
        _handle_legacy_forest(row_data, context, dataframes): Handles the legacy forest.
        _update_disturbance_timing(row_data, context, dataframes): Updates the disturbance timing.
        get_legacy_forest_area_breakdown(): Returns the breakdown of legacy forest area.
        legacy_disturbance_tracker(tracker, years): Tracks the legacy disturbances in the given years.
    """
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        afforesataion_annual_data,
        scenario_data,
    ):
        
        self.disturbance_class = Disturbances(config_path, calibration_year, forest_end_year, afforestation_data, scenario_data)

        self.forest_end_year = forest_end_year
        
        self.calibration_year = calibration_year
        self.loader_class = Loader()
        self.data_manager_class = DataManager(
            calibration_year, config_path, scenario_data
        )

        self.forest_baseline_year = self.data_manager_class.get_forest_baseline_year()

        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.afforestation_data = afforestation_data
        self.afforestation_data_annual = afforesataion_annual_data

        self.inventory_class = ForSimInventory(
            calibration_year, config_path, afforestation_data
        )

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.disturbance_dataframe = self.loader_class.disturbance_data()
        self.scenario_disturbance_dict = self.data_manager_class.scenario_disturbance_dict
        self.legacy_disturbance_dict = self.data_manager_class.get_legacy_disturbance_dict()
        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()

    
    def _scenario_afforestation_area(self, scenario):
        """
        Calculate the afforestation area for each species and year in the given scenario.

        Args:
            scenario (str): The scenario for which to calculate the afforestation area.

        Returns:
            dict: A dictionary containing the afforestation area for each species and year.
                  The keys of the dictionary are the years relative to the calibration year,
                  and the values are nested dictionaries where the keys are species names
                  and the values are the corresponding afforestation areas.
        """
        result_dict = {}

        classifiers = self.data_manager_class.config_data
        for year in self.afforestation_data_annual.year.unique():

            key = year - self.calibration_year

            result_dict[key] = {}

            for species in parser.get_inventory_species(classifiers):
                mask = (self.afforestation_data_annual["species"] == species) & (
                    self.afforestation_data_annual["scenario"] == scenario
                ) & (self.afforestation_data_annual["year"] == year)

                result_dict[key][species] = {}
                result_dict[key][species]["mineral"] = (
                    self.afforestation_data_annual.loc[mask, "total_area"].item()
                )

        return result_dict

    def legacy_disturbance_afforestation_area(self, years):
        """
        Calculate the afforestation area resulting from legacy disturbances over the given years.

        Parameters:
            years (int): The number of years to consider for calculating the afforestation area.

        Returns:
            float: The afforestation area resulting from legacy disturbances.
        """
        return self.disturbance_class.legacy_disturbance_afforestation_area(years)


    def disturbance_structure(self):
        """
        Returns the disturbance structure of the forest simulation.

        Returns: The disturbance structure.
        """
        return self.disturbance_class.disturbance_structure()

    def fill_legacy_data(self):
        """
        Fills the legacy data for the disturbance class.

        Returns:
            The filled legacy data.
        """
        return self.disturbance_class.fill_legacy_data()


    def fill_baseline_forest(self):
        """
        Fills the baseline forest with disturbances.

        Returns:
            The filled baseline forest.
        """
        return self.disturbance_class.fill_baseline_forest()


    def fill_scenario_data(self, scenario):
        """
        Fills the scenario data for disturbances in the forest simulation.

        Args:
            scenario: The scenario for which the data is being filled.

        Returns:
            disturbance_df: The DataFrame containing the filled disturbance data.
        """
        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self._scenario_afforestation_area(scenario)

        disturbance_timing = self.disturbance_timing 

        disturbance_df = self.fill_legacy_data()

        legacy_end_year = self.calibration_year - self.forest_baseline_year

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(
            range((legacy_end_year + 1), (legacy_end_year + (scenario_years + 1)))
        )

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for key, yr in enumerate(years):
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
                            
                            dataframes = {"afforestation_inventory":afforestation_inventory[key +1]}

                            self._process_scenario_row_data(row_data,context, dataframes)

                            self.disturbance_class._process_scenario_harvest_data(tracker, row_data, context)

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

                    self.disturbance_class._process_scenario_row_data(row_data,context, dataframes)

                    data.append(row_data)

        scenario_disturbance_df = pd.DataFrame(data)
        disturbance_df = pd.concat(
            [disturbance_df, scenario_disturbance_df], axis=0, ignore_index=True
        )
        disturbance_df = self.disturbance_class._drop_zero_area_rows(disturbance_df)

        return disturbance_df


    def _process_scenario_harvest_data(self, tracker, row_data, context):
        """
        Process the harvest data for a scenario.

        Args:
            tracker (Tracker): The tracker object for tracking forest for harvest.
            row_data (dict): The row data containing information about the harvest.
            context (dict): The context containing additional information.

        Returns:
            The result of processing the harvest data.
        """
        return self.disturbance_class._process_scenario_harvest_data(tracker, row_data, context)


    def _track_scenario_harvest(self, tracker, row_data, context):
        """
        Track the scenario harvest using the given tracker, row data, and context.

        Args:
            tracker: The tracker object used to track the harvest.
            row_data: The row data containing information about the harvest.
            context: The context object containing additional information.

        Returns:
            The result of the `_track_scenario_harvest` method of the disturbance class.
        """
        return self.disturbance_class._track_scenario_harvest(tracker, row_data, context)


    def _drop_zero_area_rows(self, disturbance_df):
        """
        Drops rows from the disturbance dataframe that have zero area.
        
        Args:
            disturbance_df (pandas.DataFrame): The disturbance dataframe.
            
        Returns:
            pandas.DataFrame: The disturbance dataframe with zero area rows dropped.
        """
        return self.disturbance_class._drop_zero_area_rows(disturbance_df)


    def _get_legacy_classifier_combinations(self):
        """
        Get the legacy classifier combinations.

        Returns:
            The legacy classifier combinations.
        """
        return self.disturbance_class._get_legacy_classifier_combinations()
    
    def _get_scenario_classifier_combinations(self):
        """
        Get the scenario classifier combinations.

        Returns:
            A list of scenario classifier combinations.
        """
        return self.disturbance_class._get_scenario_classifier_combinations()


    def _get_classifier_combinations(self):
        """
        Get the combinations of classifiers used for disturbance classification.
        
        Returns:
            list: A list of tuples representing the combinations of classifiers.
        """
        return self.disturbance_class._get_classifier_combinations()
    

    def _get_static_defaults(self):
        """
        Get the static defaults for the disturbance class.

        Returns:
            dict: A dictionary containing the static defaults for the disturbance class.
        """
        return self.disturbance_class._get_static_defaults()


    def _generate_row(self, species, forest_type, soil, yield_class, dist, yr):
        """
        Generate a row of data for a specific disturbance event.

        Args:
            species (str): The species of the forest.
            forest_type (str): The type of forest.
            soil (str): The type of soil.
            yield_class (int): The yield class of the forest.
            dist (str): The type of disturbance.
            yr (int): The year of the disturbance event.

        Returns:
            object: The generated row of data for the disturbance event.
        """
        return self.disturbance_class._generate_row(species, forest_type, soil, yield_class, dist, yr)


    def _process_scenario_row_data(self, row_data, context, dataframes):
        """
        Process the row data for a scenario.

        Args:
            row_data (dict): The row data for the scenario.
            context (dict): The context information for the scenario.
            dataframes (dict): The dataframes used for processing.

        Returns:
            The processed scenario row data.
        """
        return self.disturbance_class._process_scenario_row_data(row_data, context, dataframes)


    def _process_row_data(self, row_data, context, dataframes):
        """
        Process the row data using the disturbance class.

        Args:
            row_data (dict): The row data to be processed.
            context (dict): The context information for the processing.
            dataframes (dict): The dataframes used for processing.

        Returns:
            The processed row data.
        """
        return self.disturbance_class._process_row_data(row_data, context, dataframes)


    def _handle_legacy_scenario_forest(self, row_data, context, dataframes):
        """
        Handle the legacy scenario forest.

        Args:
            row_data (dict): The row data.
            context (dict): The context.
            dataframes (dict): The dataframes.

        Returns:
            The result of `_handle_legacy_scenario_forest` method of the disturbance class.
        """
        return self.disturbance_class._handle_legacy_scenario_forest(row_data, context, dataframes)


    def _handle_scenario_afforestation(self, row_data, context, dataframes):
        """
        Handle the scenario of afforestation.

        Args:
            row_data (dict): The row data for the afforestation scenario.
            context (dict): The context data for the afforestation scenario.
            dataframes (dict): The dataframes used in the afforestation scenario.

        Returns:
            The result of the _handle_scenario_afforestation method of the disturbance class.
        """
        return self.disturbance_class._handle_scenario_afforestation(row_data, context, dataframes)


    def _handle_legacy_afforestation(self, row_data, context, dataframes):
        """
        Handles legacy afforestation by calling the corresponding method in the disturbance class.

        Args:
            row_data (dict): The row data containing information about the afforestation event.
            context (dict): The context data for the simulation.
            dataframes (dict): The dataframes used in the simulation.

        Returns:
            The result of the `_handle_legacy_afforestation` method in the disturbance class.
        """
        return self.disturbance_class._handle_legacy_afforestation(row_data, context, dataframes)
      


    def _handle_legacy_forest(self, row_data, context, dataframes):
        """
        Handle legacy forest data.

        This method delegates the handling of legacy forest data to the disturbance class.

        Args:
            row_data (dict): The row data for the forest.
            context (dict): The context data for the simulation.
            dataframes (dict): The dataframes used in the simulation.

        Returns:
            The result of the disturbance class's `_handle_legacy_forest` method.
        """
        return self.disturbance_class._handle_legacy_forest(row_data, context, dataframes)

    
    def _update_disturbance_timing(self, row_data, context, dataframes):
        """
        Updates the timing of disturbances for the given row data, context, and dataframes.

        Args:
            row_data (dict): The row data containing information about the disturbances.
            context (dict): The context information for the disturbances.
            dataframes (dict): The dataframes containing the disturbance data.

        Returns:
            The updated disturbance timing.
        """
        return self.disturbance_class._update_disturbance_timing(row_data, context, dataframes)
           

    def get_legacy_forest_area_breakdown(self):
        """
        Get the breakdown of legacy forest area by disturbance class.
        
        Returns:
            dict: A dictionary containing the breakdown of legacy forest area by disturbance class.
        """
        return self.disturbance_class.get_legacy_forest_area_breakdown()
    

    def legacy_disturbance_tracker(self, tracker, years):
        """
        Apply legacy disturbances to the forest tracker.

        Parameters:
        - tracker: The disturbance tracker object.
        - years: The number of years to track disturbances.

        Returns:
        None
        """
        self.disturbance_class.legacy_disturbance_tracker(tracker, years)
            

