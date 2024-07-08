"""
Historic Afforestation Runner Module
====================================
This module provides functionalities to run historic afforestation simulations using the Carbon Budget Model (CBM).

This class is designed to facilitate the execution of Carbon Budget Model (CBM) simulations for assessing historic afforestation efforts in Ireland.

The module is intended largely for validation of historic afforestation input data, leveraging a suite of data management and simulation tools to prepare, execute, and analyze CBM simulations.
"""
from goblin_cbm_runner.default_runner.cbm_data_factory import DataFactory
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.resource_manager.paths import Paths
from goblin_cbm_runner.cbm.cbm_methods import CBMSim


import pandas as pd


class HistoricAfforRunner:
    """
    Facilitates the execution of Carbon Budget Model (CBM) simulations for assessing historic afforestation efforts in Ireland. 
    Designed primarily for the validation of historic afforestation input data, this class leverages a suite of data management and 
    simulation tools to prepare, execute, and analyze CBM simulations. It focuses on generating outputs such as carbon stocks 
    and fluxes across various afforestation scenarios, offering insights into the carbon budget implications of past afforestation activities.

    Args:
        config_path (str): The path to the configuration file.
        calibration_year (int): The year to calibrate the CBM model.
        afforest_data (dict): A dictionary containing afforestation data.
        scenario_data (dict): A dictionary containing scenario data.
        sit_path (str): The path to the SIT file.

    Attributes:
        paths_class (Paths): An instance of the Paths class for managing file paths.
        path (str): The path to the generated input data.
        baseline_conf_path (str): The path to the baseline configuration file.
        sc_fetcher (ScenarioDataFetcher): An instance of the ScenarioDataFetcher class for fetching scenario data.
        forest_end_year (int): The end year of the afforestation period.
        cbm_data_class (DataFactory): An instance of the DataFactory class for generating CBM input data.
        data_manager_class (DataManager): An instance of the DataManager class for managing data.
        INDEX (list): A list of scenario indices.
        SIM_class (CBMSim): An instance of the CBMSim class for running CBM simulations.
        years (list): A list of scenario years.
        year_range (list): A list of scenario years range.
        defaults_db (str): The path to the defaults database.


    Methods:
        generate_input_data():
            Prepares the input data necessary for CBM simulations, establishing a clean and organized data environment for scenario execution.        
        
        run_flux_scenarios():
            Executes simulations to calculate carbon flux data across different scenarios, merging and aggregating results to analyze carbon dynamics.
        
        run_aggregate_scenarios():
            Conducts simulations to generate aggregate carbon stock data from various scenarios.
        
        run_libcbm_flux_scenarios():
            Utilizes the libCBM tool own flux method to generate fluxes. 

        run_baseline_raw():
            Conducts a baseline flux simulation using the libcbm internal flux method.

        run_baseline_summary_flux():
            Generates baseline managed forest data, calculates the baseline stock, and then calculates the fluxes.

            
    """
    def __init__(
        self,
        config_path,
        calibration_year,
        afforest_data,
        scenario_data,
        sit_path=None
    ):  
        self.paths_class = Paths(sit_path, gen_baseline=True)
        self.paths_class.setup_historic_affor_paths(sit_path)
        self.path = self.paths_class.get_generated_input_data_path()
        self.baseline_conf_path = self.paths_class.get_baseline_conf_path()

        self.sc_fetcher = ScenarioDataFetcher(scenario_data)
        self.forest_end_year = self.sc_fetcher.get_afforestation_end_year()

        self.cbm_data_class = DataFactory(
            config_path, calibration_year, self.forest_end_year, afforest_data, scenario_data
        )


        self.data_manager_class = DataManager(calibration_year, config_path)

        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()

        self.SIM_class = CBMSim()

        self.years = self.data_manager_class.get_scenario_years(self.forest_end_year)

        self.year_range = self.data_manager_class.get_scenario_years_range(self.forest_end_year)

        self.defaults_db = self.paths_class.get_aidb_path()

        self.baseline_years = self.data_manager_class.get_baseline_years(self.forest_end_year)

        self.baseline_year_range = self.data_manager_class.get_baseline_years_range(self.forest_end_year)


    def _generate_base_input_data(self):
        """
        Generates the base input data for the CBM runner.

        This method cleans the baseline data directory, and then generates various input files
        required for the CBM runner, such as classifiers, configuration JSON, age classes,
        yield curves, inventory, disturbance events, disturbance types, and transition rules.

        Args:
            None

        Returns:
            None
        """
        path = self.baseline_conf_path

        if self.paths_class.is_path_internal(path):
            self.cbm_data_class.clean_baseline_data_dir(path)

        self.cbm_data_class.make_base_classifiers(path)
        self.cbm_data_class.make_config_json(None, path)
        self.cbm_data_class.make_base_age_classes(path)
        self.cbm_data_class.make_base_yield_curves(path)
        self.cbm_data_class.make_base_inventory(path)
        self.cbm_data_class.make_base_disturbance_events(path)
        self.cbm_data_class.make_base_disturbance_type(path)
        self.cbm_data_class.make_base_transition_rules(path)

    def generate_input_data(self):
        """
        Generates input data for the CBM runner.

        This method cleans the data directory, creates necessary directories,
        and generates various input files required for the CBM runner.

        Args:
            None

        Returns:
            None
        """
        path = self.path

        if self.paths_class.is_path_internal(path):
            self.cbm_data_class.clean_data_dir(path)

        self.cbm_data_class.make_data_dirs(self.INDEX, path)

        for i in self.INDEX:
            self.cbm_data_class.make_classifiers(i, path)
            self.cbm_data_class.make_config_json(i, path)
            self.cbm_data_class.make_age_classes(i, path)
            self.cbm_data_class.make_yield_curves(i, path)
            self.cbm_data_class.make_inventory(i, path)
            self.cbm_data_class.make_disturbance_events(i, path)
            self.cbm_data_class.make_disturbance_type(i, path)
            self.cbm_data_class.make_transition_rules(i, path)


    def run_flux_scenarios(self):
        """
        Conducts CBM simulations to calculate and aggregate carbon flux data.

        Returns:
            pd.DataFrame: Aggregated carbon flux data across all scenarios.

        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                      self.years, 
                                                                      self.year_range, 
                                                                      self.path,
                                                                      self.defaults_db
                                                                      )


            fluxes_data = self.SIM_class.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data


    def run_aggregate_scenarios(self):
        """
        Executes CBM simulations for a set of scenarios, generating and aggregating carbon stock data across scenarios.

        Returns:
            pd.DataFrame: Aggregated carbon stock data across all scenarios.
        """
        forest_data = pd.DataFrame()
        aggregate_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                      self.years, 
                                                                      self.year_range, 
                                                                      self.path,
                                                                      self.defaults_db
                                                                      )

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data

    def run_libcbm_flux_scenarios(self):
        """
        Conducts CBM simulations using the libcbm internal flux method.

        Returns:
            pd.DataFrame: Aggregated carbon flux data across all scenarios.

        """
        forest_data = pd.DataFrame()
        aggregate_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.SIM_class.libcbm_scenario_fluxes(i, self.cbm_data_class, 
                                                                      self.years, 
                                                                      self.year_range, 
                                                                      self.path,
                                                                      self.defaults_db)

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data


    def run_baseline_raw(self):
        """
        Conducts a baseline flux simulation using the libcbm internal flux method.

        Returns:
            pd.DataFrame: carbon flux data for the baseline scenario.

        """
        self._generate_base_input_data()
        forest_data = pd.DataFrame()
        forest_data = self.SIM_class.baseline_simulate_stock_raw_output(self.cbm_data_class,
                                                                self.baseline_years,
                                                                self.baseline_year_range,
                                                                self.baseline_conf_path,
                                                                self.defaults_db)


        return forest_data
    

    def run_baseline_summary_flux(self):
        """
        Generated the baseline managed forest data, calculates the baselines stock, before the fluxes are calculated

        Returns:
            pd.DataFrame: carbon flux data for the baseline managed forest.

        """
        self._generate_base_input_data()
   
        forest_data = self.SIM_class.baseline_simulate_stock(self.cbm_data_class,
                                                             self.baseline_years,
                                                                self.baseline_year_range,
                                                                self.baseline_conf_path,
                                                                self.defaults_db)
        
        fluxes_data = self.SIM_class.cbm_baseline_summary_fluxes(forest_data)

        return fluxes_data
    
