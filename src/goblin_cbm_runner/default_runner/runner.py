"""
Runner Module
=============
This module orchestrates the execution of Carbon Budget Model (CBM) simulations for various scenarios,
including baseline and afforestation projects.

"""
from goblin_cbm_runner.cbm.data_processing.default_processing.cbm_data_factory import DataFactory
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.resource_manager.paths import Paths
from goblin_cbm_runner.cbm.methods.cbm_methods import CBMSim

import pandas as pd

class Runner:
    """
    The Runner class orchestrates the execution of Carbon Budget Model (CBM) simulations 
    for various scenarios, including baseline, afforestation, and user-defined forest management strategies.
    It utilizes annualized data to estimate carbon stock or flux over specified years.
    
    This class manages input data preparation, CBM simulation setups, and the execution process, generating outputs like carbon stocks and fluxes for various scenarios.

    Args:
        data_manager (DataManager): Instance of DataManager for managing simulation data and configurations.

    Attributes:
        paths_class (Paths): Instance of Paths for setting up directory paths for CBM simulation input data.
        sit_path (str): Path to the SIT directory.
        defaults_db (str): Path to the default database.
        path (str): Directory path where input data is stored.
        baseline_conf_path (str): Directory path for baseline configuration data.
        cbm_data_class (DataFactory): Instance of DataFactory for preparing CBM data.
        sc_fetcher (ScenarioDataFetcher): Instance of ScenarioDataFetcher for fetching scenario data.
        forest_end_year (int): The final year of the forest simulation period.
        INDEX (list): List of unique identifiers for each simulation scenario.
        SIM_class (CBMSim): Instance of CBMSim for running CBM simulations.
        historic_scenario_years (list): List of years for historic scenarios.
        historic_scenario_year_range (range): Range of years for historic scenarios.
        baseline_years (list): List of years for baseline scenarios.
        baseline_year_range (range): Range of years for baseline scenarios.
        scenario_years (list): List of years for user-defined scenarios.
        scenario_year_range (range): Range of years for user-defined scenarios.
        forest_FM_baseline_dataframe (pd.DataFrame): DataFrame containing forest management baseline data.
        forest_AF_baseline_dataframe (pd.DataFrame): DataFrame containing afforestation baseline data.
        merged_AF_FM_forest_data (pd.DataFrame): DataFrame containing merged afforestation and forest management data.
        afforestation_dataframe (pd.DataFrame): DataFrame containing afforestation data for all scenarios.

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
        data_manager
    ):
        self.data_manager_class = data_manager

        self.sit_path = self.data_manager_class.get_sit_path()

        self.paths_class = Paths(self.sit_path, gen_baseline=True)
        self.paths_class.setup_runner_paths(self.sit_path)

        self.defaults_db = self.paths_class.get_aidb_path()

        self.path = self.paths_class.get_generated_input_data_path()

        self.baseline_conf_path = self.paths_class.get_baseline_conf_path()
        
        self.sc_fetcher = ScenarioDataFetcher(data_manager)

        self.cbm_data_class = DataFactory(data_manager)

        self.forest_end_year = self.data_manager_class.get_forest_end_year()

        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()
        
        self.SIM_class = CBMSim()

        self.historic_scenario_years = self.data_manager_class.get_full_scenario_years(self.forest_end_year)

        self.historic_scenario_year_range = self.data_manager_class.get_full_scenario_years_range(self.forest_end_year)

        self.baseline_years = self.data_manager_class.get_baseline_years(self.forest_end_year)

        self.baseline_year_range = self.data_manager_class.get_baseline_years_range(self.forest_end_year)

        self.scenario_years = self.data_manager_class.calculate_scenario_years(self.forest_end_year)

        self.scenario_year_range = self.data_manager_class.calculate_scenario_years_range(self.forest_end_year)

        self._generate_FM_input_data()
        self.forest_FM_baseline_dataframe = self.SIM_class.FM_simulate_stock(self.cbm_data_class,
                                                                                 self.baseline_years,
                                                                                 self.baseline_year_range,
                                                                                 self.baseline_conf_path,
                                                                                 self.defaults_db)

        self._generate_input_data()

        self.forest_AF_baseline_dataframe = self.SIM_class.cbm_aggregate_scenario_stock(-1, self.cbm_data_class, 
                                                                                        self.historic_scenario_years, 
                                                                                        self.historic_scenario_year_range, 
                                                                                        self.path,
                                                                                        self.defaults_db
                                                                                        )

        self.merged_AF_FM_forest_data = self.merge_forest_AF_FM_dataframes()

        self.afforestation_dataframe = self._generate_afforestation_dataframe()


    def get_afforestation_dataframe(self):
        """
        Returns the afforestation data for all scenarios.

        Returns:
            pd.DataFrame: Afforestation data for all scenarios.
        """
        return self.afforestation_dataframe

    def _generate_afforestation_dataframe(self):
        """
        Generates the afforestation data for all scenarios.

        Returns:
            pd.DataFrame: Afforestation data for all scenarios.
        """
        path =self.path

        afforestation_dataframe = pd.DataFrame()

        for i in self.INDEX:
            data = self.SIM_class.get_scenario_afforestation_rates(i, path)
            afforestation_dataframe = pd.concat([afforestation_dataframe, data], ignore_index=True)

        return afforestation_dataframe
    

    def _generate_FM_input_data(self):
        """
        Generates the base input data for the CBM runner.

        This method cleans the baseline data directory, and then generates various input files
        required for the CBM runner, such as classifiers, configuration JSON, age classes,
        yield curves, inventory, disturbance events, disturbance types, and transition rules.

        Returns:
            None
        """
        path = self.baseline_conf_path

        if self.paths_class.is_path_internal(path):
            self.cbm_data_class.clean_baseline_data_dir(path)

        self.cbm_data_class.make_FM_classifiers(path)
        self.cbm_data_class.make_config_json(None, path)
        self.cbm_data_class.make_FM_age_classes(path)
        self.cbm_data_class.make_FM_yield_curves(path)
        self.cbm_data_class.make_FM_inventory(path)
        self.cbm_data_class.make_FM_disturbance_events(path)
        self.cbm_data_class.make_FM_disturbance_type(path)
        self.cbm_data_class.make_FM_transition_rules(path)


    def _generate_input_data(self):
        """
        Generates input data for the CBM runner.

        This method cleans the data directory, creates necessary directories,
        and generates various input files required for the CBM runner.

        Returns:
            None
        """
        path = self.path
    
        if self.paths_class.is_path_internal(path):
            print("Cleaning scenario SIT data directories")
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


    @property
    def get_AF_baseline_dataframe(self):
        """
        Returns the baseline data for afforestation scenarios.

        Returns:
            pd.DataFrame: Baseline data for afforestation scenarios.
        """
        return self.forest_AF_baseline_dataframe
    
    @property
    def get_FM_baseline_dataframe(self):
        """
        Returns the baseline data for user-defined forest management scenarios.

        Returns:
            pd.DataFrame: Baseline data for user-defined forest management scenarios.
        """
        return self.forest_FM_baseline_dataframe
    

    @property
    def get_merged_forest_AF_FM_dataframes(self):
        """
        Returns the merged data for afforestation and user-defined forest management scenarios.

        Returns:
            pd.DataFrame: Merged data for afforestation and forest management baseline scenarios.
        """
        return self.merged_AF_FM_forest_data
    

    def merge_forest_AF_FM_dataframes(self):
        """
        Merges the baseline data for afforestation and user-defined forest management scenarios.

        This method merges the afforestation and forest management baseline dataframes on the 'Year' column,
        and sums the specified columns for the shared years.

        Returns:
            pd.DataFrame: Merged data for afforestation and forest management baseline scenarios.

        """
        # Merge the dataframes on 'Year'
        merged_data = pd.merge(self.get_AF_baseline_dataframe.copy(deep=True), 
                               self.get_FM_baseline_dataframe.copy(deep=True), 
                               on="Year", 
                               how="inner",
                               suffixes=("_AF", "_FM"))
        
        # Sum the specified columns for the shared years
        columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        for col in columns_to_add:
            merged_data[col] = merged_data[col + "_AF"] + merged_data[col + "_FM"]
            merged_data.drop(columns=[col + "_AF", col + "_FM"], inplace=True)
        
        return merged_data


    def run_aggregate_scenarios(self):
        """
        Executes CBM simulations for a set of scenarios, generating and aggregating carbon stock data across scenarios, including those derived from user-defined forest management strategies.

        Merges scenario-specific data with baseline data to provide a comprehensive view of carbon stocks under various management strategies.

        Returns:
            pd.DataFrame: Aggregated carbon stock data across all scenarios.
        """
        
        forest_data = pd.DataFrame()
        aggregate_forest_data = pd.DataFrame()

        FM_AF_forest_data = self.get_merged_forest_AF_FM_dataframes.copy(deep=True)

        columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]

        for i in self.INDEX:

            if i > -1:
                forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                        self.scenario_years, 
                                                                        self.scenario_year_range, 
                                                                        self.path,
                                                                        self.defaults_db
                                                                        )

                # Assuming 'year' is the common column
                merged_data = pd.merge(
                    forest_data,
                    FM_AF_forest_data,
                    on="Year",
                    how="inner",
                    suffixes=("", "_baseline"),
                )


                # Add the values for selected columns where 'year' matches
                for col in columns_to_add:
                    merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]
                    
                # Drop all columns with '_baseline' suffix
                columns_to_drop = [col for col in merged_data.columns if col.endswith('_baseline')]
                merged_data.drop(columns=columns_to_drop, inplace=True)

                # Update the original 'forest_data' DataFrame with the merged and added data
                forest_data = merged_data
            else:
                forest_data = FM_AF_forest_data

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data], ignore_index=True
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

        columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]

        FM_AF_forest_data = self.get_merged_forest_AF_FM_dataframes.copy(deep=True)

        for i in self.INDEX:
            print(f"Running Forest Flux scenario {i}")
            if i > -1:
                forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                        self.scenario_years, 
                                                                        self.scenario_year_range, 
                                                                        self.path,
                                                                        self.defaults_db
                                                                        )

                # Assuming 'year' is the common column
                merged_data = pd.merge(
                    forest_data,
                    FM_AF_forest_data,
                    on="Year",
                    how="inner",
                    suffixes=("", "_baseline"),
                )


                # Add the values for selected columns where 'year' matches
                for col in columns_to_add:
                    merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]

                # Drop all columns with '_baseline' suffix
                columns_to_drop = [col for col in merged_data.columns if col.endswith('_baseline')]
                merged_data.drop(columns=columns_to_drop, inplace=True)


                # Update the original 'forest_data' DataFrame with the merged and added data
                forest_data = merged_data
            else:
                forest_data = FM_AF_forest_data


            fluxes_data = self.SIM_class.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data


    def run_sep_flux_scenarios(self):
        """
        Conducts CBM simulations to calculate and separate carbon flux data for various scenarios, including those with user-defined forest management strategies.

        This process helps in understanding the impact of different management practices on carbon dynamics within forest ecosystems.

        Returns:
            dict: Separated carbon flux data across all scenarios.
        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        FM_forest_data = self.get_FM_baseline_dataframe

        FM_forest_data["Scenario"] = 999

        FM_forest_data = self.SIM_class.cbm_scenario_fluxes(FM_forest_data)

        AF_forest_data = self.get_AF_baseline_dataframe

        AF_forest_data = self.SIM_class.cbm_scenario_fluxes(AF_forest_data)

        AM_AF_forest_data = self.get_merged_forest_AF_FM_dataframes

        AM_AF_forest_data["Scenario"] = 999

        AM_AF_forest_data = self.SIM_class.cbm_scenario_fluxes(AM_AF_forest_data)


        for i in self.INDEX:
            if i > -1:
                forest_data = self.SIM_class.cbm_aggregate_scenario_stock(i, self.cbm_data_class, 
                                                                        self.scenario_years, 
                                                                        self.scenario_year_range, 
                                                                        self.path,
                                                                        self.defaults_db
                                                                        )


            fluxes_data = self.SIM_class.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return {"AF": AF_forest_data, "FM": FM_forest_data, "AM_AF": AM_AF_forest_data, "SC": fluxes_forest_data}