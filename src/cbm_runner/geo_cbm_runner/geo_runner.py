"""
Geo CBM Runner Module
=====================
This module provides functionalities to run CBM simulations focused on Irish historic afforestation at the catchment level, 
utilizing geo-specific data preparation and management for Irish catchment data.

"""
from cbm_runner.geo_cbm_runner.geo_cbm_data_factory import DataFactory
from cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from cbm_runner.resource_manager.paths import Paths
from cbm_runner.cbm.cbm_methods import CBMSim


import pandas as pd


class GeoRunner:
    """
    Handles execution of CBM simulations focused on Irish historic afforestation at the catchment level, utilizing 
    geo-specific data preparation and management for Irish catchment data. This class orchestrates the setup, execution, 
    and output generation for various scenarios, providing insights into carbon stocks and fluxes.

    Args:
        config_path (str): Path to the configuration file.
        calibration_year (int): Year used for calibration.
        afforest_data (AfforestData): Afforestation data.
        scenario_data (ScenarioData): Scenario data.
        gen_baseline (bool): Flag to generate baseline data.
        gen_validation (bool): Flag to generate validation data.
        validation_path (str): Path to directory for validation data.
        sit_path (str): Path to the SIT directory.

    Attributes:
        paths_class (Paths): Manages paths for the GeoRunner.
        gen_validation (bool): Flag to generate validation data.
        validation_path (str): Path to directory for validation data.
        path (str): Path to directory for input data.
        baseline_conf_path (str): Path to directory for baseline configuration data.
        cbm_data_class (DataFactory): Handles CBM data preparation.
        data_manager_class (GeoDataManager): Manages simulation data and configurations.
        INDEX (list): Identifiers for each afforestation scenario.
        forest_end_year (int): End year for the simulation period.
        pools (Pools): Manages CBM carbon pools.
        Flux_class (FluxManager): Calculates carbon fluxes.
        AGB, BGB, deadwood, litter, soil: Represent various carbon pool types in CBM simulations.

    Methods:
        __init__(config_path, calibration_year, afforest_data, scenario_data, gen_baseline=True, gen_validation=False, validation_path=None):
            Initializes the GeoRunner with configuration paths, data, and operational flags.

        generate_base_input_data():
            Prepares baseline data for simulations, involving directory cleanup and input file generation.

        generate_input_data():
            Creates scenario-specific input data after cleaning the directory and setting up necessary subdirectories.

        afforestation_scenarios_structure():
            Retrieves structural data for each scenario, aiding in detailed analysis.

        run_flux_scenarios():
            Executes simulations to calculate carbon flux data across scenarios.

        run_aggregate_scenarios():
            Generates and aggregates carbon stock data from simulations across scenarios.

        cbm_baseline_forest():
            Conducts a baseline forest simulation, returning stock, structure, and raw data.

        cbm_aggregate_scenario(sc):
            Produces carbon stock data for a specified scenario, along with structure and raw data.

        libcbm_scenario_fluxes(sc):
            Generates carbon fluxes using the Libcbm method for specified scenarios.

        cbm_scenario_fluxes(forest_data):
            Calculates carbon fluxes based on forest data for each scenario.

    Note:
        An external path can be specified to generate the validation data.

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


        self.generate_base_input_data()
        self.forest_baseline_dataframe = self.SIM_class.baseline_simulate_stock(self.cbm_data_class,
                                                                            self.baseline_years,
                                                                            self.baseline_year_range,
                                                                            self.baseline_conf_path,
                                                                            self.defaults_db)


    def generate_base_input_data(self):
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

        
        if not self.paths_class.is_path_internal(path):
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
        Runs aggregate scenarios for forest data.

        This method iterates over a set of scenarios and generates carbon stock data for each scenario.
        It merges the forest data with a baseline forest data, adds selected columns, and drops duplicate columns.
        The carbon stock data for all scenarios is then concatenated into a single DataFrame.

        Returns:
            pd.DataFrame: The carbon stock data for all scenarios.
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
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
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
        Runs carbon flux scenarios for each index in self.INDEX.

        Returns:
            pandas.DataFrame: A DataFrame containing the merged and added data from each scenario.
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
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
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
        
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()

        years_data = {
        "Year": [(forest_baseline_year-2), (forest_baseline_year-1)],
        "AGB": [0.0, 0.0],
        "BGB": [0.0, 0.0],
        "Deadwood": [0.0, 0.0],
        "Litter": [0.0, 0.0],
        "Soil": [0.0, 0.0],
        "Total Ecosystem": [0.0, 0.0],
        "Scenario": [sc, sc]  # Assuming 'sc' is defined somewhere in your code
        }
        
        return pd.DataFrame(years_data)
