"""
Geo CBM Runner Module
=====================
This module provides functionalities to run CBM simulations focused on Irish historic afforestation at the catchment level, 
utilizing geo-specific data preparation and management for Irish catchment data.

"""
from goblin_cbm_runner.geo_cbm_runner.geo_cbm_data_factory import DataFactory
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.resource_manager.paths import Paths
from goblin_cbm_runner.cbm.cbm_methods import CBMSim


import pandas as pd


class GeoRunner:
    """
    The Runner class orchestrates the execution of Carbon Budget Model (CBM) simulations 
    for various scenarios, including baseline, afforestation, and user-defined forest management strategies.
    It utilizes annualized data to estimate carbon stock or flux over specified years.
    
    This class manages input data preparation, CBM simulation setups, and the execution process, generating outputs like carbon stocks and fluxes for various scenarios.

    Args:
        config_path (str): Path to the CBM configuration file.
        calibration_year (int): Calibration year for the simulations.
        afforest_data (AfforestData): Data for afforestation scenarios.
        scenario_data (ScenarioData): Data for user-defined management scenarios.
        sit_path (str): Path to the SIT directory, optional.

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
        generate_input_data():
            Generates input data required for CBM simulations including those based on user-defined forest management strategies.
            Cleans the data directory, creates necessary subdirectories, and prepares scenario-specific input files.

        run_aggregate_scenarios():
            Executes CBM simulations for a set of scenarios including user-defined management strategies, generating and aggregating carbon stock data across these scenarios.

        run_flux_scenarios():
            Conducts CBM simulations to calculate carbon flux data for various scenarios including user-defined management strategies, merging and aggregating results.

    """
    def __init__(
        self,
        config_path,
        calibration_year,
        afforest_data,
        scenario_data,
        sit_path = None,
    ):

        self.paths_class = Paths(sit_path, gen_baseline=True)
        self.paths_class.setup_geo_runner_paths(sit_path)

        self.defaults_db = self.paths_class.get_aidb_path()

        self.path = self.paths_class.get_generated_input_data_path()

        self.baseline_conf_path = self.paths_class.get_baseline_conf_path()
        
        self.sc_fetcher = ScenarioDataFetcher(scenario_data)

        self.forest_end_year = self.sc_fetcher.get_afforestation_end_year()
       
        self.cbm_data_class = DataFactory(
            config_path, calibration_year, self.forest_end_year, afforest_data, scenario_data
        )
        self.data_manager_class = GeoDataManager(calibration_year, config_path)

        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()

        self.SIM_class = CBMSim()


        self.baseline_years = self.data_manager_class.get_baseline_years(self.forest_end_year)

        self.baseline_year_range = self.data_manager_class.get_baseline_years_range(self.forest_end_year)


        self._generate_base_input_data()
        self.forest_baseline_dataframe = self.SIM_class.baseline_simulate_stock(self.cbm_data_class,
                                                                            self.baseline_years,
                                                                            self.baseline_year_range,
                                                                            self.baseline_conf_path,
                                                                            self.defaults_db)


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

        self.cbm_data_class.make_classifiers(None, path)
        self.cbm_data_class.make_config_json(None, path)
        self.cbm_data_class.make_age_classes(None, path)
        self.cbm_data_class.make_yield_curves(None, path)
        self.cbm_data_class.make_inventory(None, path)
        self.cbm_data_class.make_disturbance_events(None, path)
        self.cbm_data_class.make_disturbance_type(None, path)
        self.cbm_data_class.make_transition_rules(None, path)


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


    def run_aggregate_scenarios(self):
        """
        Executes CBM simulations for a set of scenarios, generating and aggregating carbon stock data across scenarios, including those derived from user-defined forest management strategies.

        Merges scenario-specific data with baseline data to provide a comprehensive view of carbon stocks under various management strategies.

        Returns:
            pd.DataFrame: Aggregated carbon stock data across all scenarios.
        """
        forest_data = pd.DataFrame()
        aggregate_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                      self.baseline_years, 
                                                                      self.baseline_year_range, 
                                                                      self.path,
                                                                      self.defaults_db
                                                                      )
            additional_years = self._add_years(i)
            forest_data = pd.concat([additional_years, forest_data], ignore_index=True)

            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe,
                on="Year",
                how="inner",
                suffixes=("", "_baseline"),
            )

            # Add the values for selected columns where 'year' matches
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
            for col in columns_to_add:
                merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]

            # Drop the duplicate columns (columns with '_baseline' suffix)
            merged_data.drop(
                columns=[col + "_baseline" for col in columns_to_add], inplace=True
            )

            # Update the original 'forest_data' DataFrame with the merged and added data
            forest_data = merged_data

            forest_data_copy = forest_data.copy(deep=True)


            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data

    def run_flux_scenarios(self):
        """
        Conducts CBM simulations to calculate and aggregate carbon flux data for various scenarios, including those with user-defined forest management strategies.

        This process helps in understanding the impact of different management practices on carbon dynamics within forest ecosystems.

        Returns:
            pd.DataFrame: Aggregated carbon flux data across all scenarios.

        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                      self.baseline_years, 
                                                                      self.baseline_year_range, 
                                                                      self.path,
                                                                      self.defaults_db
                                                                      )


            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe,
                on="Year",
                how="inner",
                suffixes=("", "_baseline"),
            )

            # Add the values for selected columns where 'year' matches
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
            for col in columns_to_add:
                merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]

            # Drop the duplicate columns (columns with '_baseline' suffix)
            merged_data.drop(
                columns=[col + "_baseline" for col in columns_to_add], inplace=True
            )

            # Update the original 'forest_data' DataFrame with the merged and added data
            forest_data = merged_data

            fluxes_data = self.SIM_class.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data


    def _add_years(self,  sc):
        """
        Adds additional years to the DataFrame.

        Args:
            sc (int): Scenario index.

        Returns:
            pd.DataFrame: DataFrame with additional years.
        """
        
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()

        years_data = {
        "Year": [(forest_baseline_year-2), (forest_baseline_year-1)],
        "AGB": [0.0, 0.0],
        "BGB": [0.0, 0.0],
        "Deadwood": [0.0, 0.0],
        "Litter": [0.0, 0.0],
        "Soil": [0.0, 0.0],
        "Harvest": [0.0, 0.0],
        "Total Ecosystem": [0.0, 0.0],
        "Scenario": [sc, sc]  # Assuming 'sc' is defined somewhere in your code
        }
        
        return pd.DataFrame(years_data)
