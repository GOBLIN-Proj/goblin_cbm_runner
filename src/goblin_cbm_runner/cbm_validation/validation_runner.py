"""
Runner Module
=============
This module is responsible for orchestrating the execution of Carbon Budget Model (CBM) simulations for various scenarios,
including baseline and afforestation projects. 

"""
from goblin_cbm_runner.default_runner.cbm_data_factory import DataFactory
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.resource_manager.paths import Paths
from goblin_cbm_runner.cbm.cbm_methods import CBMSim

import pandas as pd

class ValRunner:
    """
    The Runner class orchestrates the execution of Carbon Budget Model (CBM) simulations 
    for various scenarios, including baseline and afforestation projects. It utilizes 
    annualized afforestation data to give an estimation of carbon stock or flux over a number of 
    specified years (from the calibration year to the target year).

    This class leverages various data factories and managers to prepare input data, set up, 
    and execute CBM simulations, ultimately generating outputs such as carbon stocks and fluxes 
    across different scenarios. It manages the creation and organization of simulation input data 
    using specified directory paths and configuration files.

    Args:
        config_path (str): The path to the CBM configuration file.
        calibration_year (int): The year used for calibration.
        afforest_data (AfforestData): The afforestation data.
        scenario_data (ScenarioData): The scenario data.
        gen_baseline (bool): A boolean indicating whether to generate baseline data.
        gen_validation (bool): A boolean indicating whether to generate validation data.
        sit_path (str): The path to the SIT directory.

    Attributes:
        paths_class (Paths): Instance of Paths for setting up directory paths for CBM simulation input data.
        gen_validation (bool): A boolean indicating whether to generate validation data.
        validation_path (str): Directory path for validation data.
        path (str): Directory path where input data is stored.
        baseline_conf_path (str): Directory path for baseline configuration data.
        cbm_data_class (DataFactory): Instance of DataFactory for preparing CBM data.
        data_manager_class (DataManager): Instance of DataManager for managing simulation data and configurations.
        INDEX (list): List of unique identifiers for each simulation scenario.
        forest_end_year (int): The final year of the forest simulation period.
        pools (Pools): Instance of the Pools class for managing CBM carbon pools.
        AGB, BGB, deadwood, litter, soil, flux_pools (various): Instances representing different carbon pool types used in CBM simulations.

    Methods:
        generate_base_input_data():
            Prepares baseline input data required for CBM simulations by cleaning the baseline data directory and generating essential input files.

        generate_input_data():
            Generates input data for various afforestation scenarios by cleaning the data directory, creating necessary subdirectories, and preparing scenario-specific input files.

        run_aggregate_scenarios():
            Executes CBM simulations for a set of scenarios, generating and aggregating carbon stock data across these scenarios.

        run_flux_scenarios():
            Conducts CBM simulations to calculate carbon flux data for various scenarios, merging and aggregating results.

        afforestation_scenarios_structure():
            Retrieves structural data for each afforestation scenario, facilitating analysis of scenario-specific forest dynamics.

        cbm_baseline_forest():
            Executes the CBM simulation for the baseline forest scenario, generating stock, structural, and raw simulation data.

        cbm_aggregate_scenario(sc):
            Runs a CBM simulation for a specified scenario (sc), generating aggregated carbon stock and raw data.

        cbm_scenario_fluxes(forest_data):
            Calculates carbon fluxes based on CBM simulation outputs for given forest data, aiding in the analysis of carbon dynamics across scenarios.

        libcbm_scenario_fluxes(sc):
            Generates carbon flux data using the Libcbm method directly for a specified scenario (sc), contributing to the comprehensive analysis of carbon budget impacts under different land management strategies.
   
    Note:
        An external path can be specified to generate the validation data.
    """
    def __init__(
        self,
        start_year,
        end_year,
        sit_path,
        results_path,
    ):
        self.paths_class = Paths(sit_path, gen_baseline=True)
    
        self.defaults_db = self.paths_class.get_aidb_path()

        self.path = sit_path   

   
        self.SIM_class = CBMSim()

        self.start = start_year
        self.end = end_year
        self.years = end_year - start_year + 1
        self.year_range = range(start_year, end_year + 1)



    def run_validation(self):
        """
        Runs the CBM validation for the specified years.

        Returns:
            dict: A dictionary containing the validation dataframes
        """

        data = self.SIM_class.cbm_basic_validation(self.years, 
                                                    self.path,
                                                    self.defaults_db
                                                    )
            
        return data


    def run_flux_validation(self, forest_data):
        """
        Runs the CBM validation for the specified years.

        Returns:
            dict: A dictionary containing the validation dataframes
        """

        forest_data.groupby("timestep").sum()
        
        data = self.SIM_class.forest_raw_fluxes(forest_data)
            
        return data