"""
Historic Afforestation Runner Module
====================================
This module provides functionalities to run historic afforestation simulations using the Carbon Budget Model (CBM).

This class is designed to facilitate the execution of Carbon Budget Model (CBM) simulations for assessing historic afforestation efforts in Ireland.

The module is intended largely for validation of historic afforestation input data, leveraging a suite of data management and simulation tools to prepare, execute, and analyze CBM simulations.
"""
import historic_affor.generated_input_data as input_data_path
import historic_affor.baseline_input_conf as baseline_conf_path
from cbm_runner.cbm_data_factory import DataFactory
from resource_manager.cbm_runner_data_manager import DataManager
from resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from cbm_runner.runner import Runner


import pandas as pd


class HistoricAfforRunner:
    """
    Facilitates the execution of Carbon Budget Model (CBM) simulations for assessing historic afforestation efforts in Ireland. 
    Designed primarily for the validation of historic afforestation input data, this class leverages a suite of data management and 
    simulation tools to prepare, execute, and analyze CBM simulations. It focuses on generating outputs such as carbon stocks 
    and fluxes across various afforestation scenarios, offering insights into the carbon budget implications of past afforestation activities.

    Attributes:
        path (str): Directory path where input data is stored, facilitating data management and simulation setup.
        baseline_conf_path (str): Directory path for baseline configuration data, critical for initializing simulation parameters.
        cbm_data_class (DataFactory): Manages the creation and organization of CBM data, ensuring accurate simulation inputs.
        data_manager_class (DataManager): Oversees data retrieval and configuration, aligning simulation data with scenario requirements.
        INDEX (list): Collection of unique identifiers for each afforestation scenario, supporting scenario-specific simulations.
        forest_end_year (int): Marks the termination year of the forest simulation, defining the temporal scope of the analysis.
        runner_class (Runner): Executes CBM simulation scenarios, generating key outputs like carbon stocks and fluxes.

    Methods:
        generate_input_data():
            Prepares the input data necessary for CBM simulations, establishing a clean and organized data environment for scenario execution.
        
        afforestation_scenarios_structure():
            Gathers structural data for each afforestation scenario, providing a comprehensive overview of scenario-specific simulation setups.
        
        run_flux_scenarios():
            Executes simulations to calculate carbon flux data across different scenarios, merging and aggregating results to analyze carbon dynamics.
        
        run_aggregate_scenarios():
            Conducts simulations to generate aggregate carbon stock data from various scenarios, facilitating a holistic analysis of carbon storage outcomes.
        
        run_libcbm_flux_scenarios():
            Utilizes the libCBM tool to run aggregate scenarios, focusing on the generation and analysis of carbon flux data within a library-based CBM framework.
        
        cbm_aggregate_scenario(scenario):
            Conducts an aggregate scenario simulation, yielding carbon stock data for scenario analysis and comparison.
        
        libcbm_scenario_fluxes(scenario):
            Invokes libCBM to calculate carbon fluxes for a given scenario, enhancing the depth of analysis with library-supported CBM functionalities.
    """
    def __init__(
        self,
        config_path,
        calibration_year,
        afforest_data,
        scenario_data,
        validation_path,
    ):
        self.path = input_data_path.get_local_dir()
        self.baseline_conf_path = baseline_conf_path.get_local_dir()

        self.sc_fetcher = ScenarioDataFetcher(scenario_data)
        self.forest_end_year = self.sc_fetcher.get_afforestation_end_year()

        self.cbm_data_class = DataFactory(
            config_path, calibration_year, self.forest_end_year, afforest_data, scenario_data
        )


        self.data_manager_class = DataManager(calibration_year, config_path)

        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()
        
        
        self.runner_class = Runner(
        config_path,
        calibration_year,
        afforest_data,
        scenario_data,
        gen_baseline=False,
        gen_validation=True,
        validation_path=validation_path)



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



    def afforestation_scenarios_structure(self):
        """
        Retrieves the structure data for each afforestation scenario.

        Returns:
            pandas.DataFrame: A DataFrame containing the structure data for each afforestation scenario.
        """
        forest_data = pd.DataFrame()
        structure_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.cbm_aggregate_scenario(i)["Structure"]
            forest_data["Scenario"] = i

            structure_data = pd.concat([structure_data, forest_data], ignore_index=True)

        return structure_data


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
            forest_data = self.runner_class.cbm_aggregate_scenario(i, path=self.path)["Stock"]


            fluxes_data = self.runner_class.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data

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
            forest_data = self.runner_class.cbm_aggregate_scenario(i, path=self.path)["Stock"]

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data

    def run_libcbm_flux_scenarios(self):
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
            forest_data = self.libcbm_scenario_fluxes(i)["Stock"]

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data

    def cbm_aggregate_scenario(self, scenario):
        """
        Runs aggregate scenarios for forest data.

        This method iterates over a set of scenarios and generates carbon stock data for each scenario.
        It merges the forest data with a baseline forest data, adds selected columns, and drops duplicate columns.
        The carbon stock data for all scenarios is then concatenated into a single DataFrame.

        Args:
            scenario (int): The scenario number.

        Returns:
            pd.DataFrame: The carbon stock data for all scenarios.
        """
        return self.runner_class.cbm_aggregate_scenario(scenario, path=self.path)
    
    def libcbm_scenario_fluxes(self, scenario):
        """
        Generate carbon Fluxes using the Libcbm method for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.

        Returns:
            dict: A dictionary containing the aggregated data.
                - "Stock": DataFrame containing annual carbon stocks.
                - "Raw": DataFrame containing raw data.
        """
        return self.runner_class.libcbm_scenario_fluxes(scenario, path=self.path)