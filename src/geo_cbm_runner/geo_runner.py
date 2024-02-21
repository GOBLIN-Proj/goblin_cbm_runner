"""
Geo CBM Runner Module
=====================
This module provides functionalities to run CBM simulations focused on Irish historic afforestation at the catchment level, 
utilizing geo-specific data preparation and management for Irish catchment data.

"""
import geo_cbm_runner.generated_input_data as input_data_path
import geo_cbm_runner.baseline_input_conf as baseline_conf_path
from geo_cbm_runner.geo_cbm_data_factory import DataFactory
from resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from resource_manager.cbm_pools import Pools
from resource_manager.flux_manager import FluxManager
from resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from cbm_validation.validation import ValidationData
from libcbm.model.cbm import cbm_simulator
from libcbm.input.sit import sit_cbm_factory


import pandas as pd


class GeoRunner:
    """
    Handles execution of CBM simulations focused on Irish historic afforestation at the catchment level, utilizing 
    geo-specific data preparation and management for Irish catchment data. This class orchestrates the setup, execution, 
    and output generation for various scenarios, providing insights into carbon stocks and fluxes.

    Attributes:
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
        """
    def __init__(
        self,
        config_path,
        calibration_year,
        afforest_data,
        scenario_data,
        gen_baseline = True,
        gen_validation = False,
        validation_path = None,
    ):
        self.gen_validation = gen_validation
        self.validation_path = validation_path
        self.path = input_data_path.get_local_dir()
        self.baseline_conf_path = baseline_conf_path.get_local_dir()
        self.sc_fetcher = ScenarioDataFetcher(scenario_data)
        self.forest_end_year = self.sc_fetcher.get_afforestation_end_year()
        self.cbm_data_class = DataFactory(
            config_path, calibration_year, self.forest_end_year, afforest_data, scenario_data
        )
        self.data_manager_class = GeoDataManager(calibration_year, config_path)

        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()

        self.pools = Pools()
        self.Flux_class = FluxManager()
        self.AGB = self.pools.get_above_ground_biomass_pools()
        self.BGB = self.pools.get_below_ground_biomass_pools()
        self.deadwood = self.pools.get_deadwood_pools()
        self.litter = self.pools.get_litter_pools()
        self.soil = self.pools.get_soil_organic_matter_pools()
        
        if validation_path is not None and gen_validation:
            ValidationData.clear_validation_folder(self.validation_path)

        if gen_baseline:
            self.generate_base_input_data()
            self.forest_baseline_dataframe = self.cbm_baseline_forest()
            if self.gen_validation:
                ValidationData.get_baseline_forest(self.validation_path, self.forest_baseline_dataframe["Stock"])


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
            forest_data = self.cbm_aggregate_scenario(i)["Stock"]

            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe["Stock"],
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
            forest_data = self.cbm_aggregate_scenario(i)["Stock"]

            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe["Stock"],
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

            fluxes_data = self.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data

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


    def cbm_baseline_forest(self):
            """
            Runs a baseline forest simulation using the CBM model.

            Returns:
                dict: A dictionary containing the following data:
                    - "Stock": DataFrame containing annual carbon stocks for different components (AGB, BGB, Deadwood, Litter, Soil, Total Ecosystem) over the simulation period.
                    - "Structure": DataFrame containing age, time since last disturbance, and last disturbance type for each timestep.
                    - "Raw": DataFrame containing raw CBM simulation results.
            """
            
            forest_baseline_year = self.data_manager_class.get_forest_baseline_year()
            forestry_end_year = self.forest_end_year
            path = self.baseline_conf_path

            years = (forestry_end_year +1) - forest_baseline_year 

            year_range = [
                year for year in range(forest_baseline_year -1, forestry_end_year +1)
            ]

            sit, classifiers, inventory = self.cbm_data_class.set_baseline_input_data_dir(
                path
            )

            classifier_config = sit_cbm_factory.get_classifiers(
                sit.sit_data.classifiers, sit.sit_data.classifier_values
            )

            results, reporting_func = cbm_simulator.create_in_memory_reporting_func(
                classifier_map={
                    x["id"]: x["value"] for x in classifier_config["classifier_values"]
                }
            )

            # Simulation
            with sit_cbm_factory.initialize_cbm(sit) as cbm:
                # Create a function to apply rule based disturbance events and transition rules based on the SIT input
                rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                    sit, cbm
                )
                # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
                cbm_simulator.simulate(
                    cbm,
                    n_steps=years,
                    classifiers=classifiers,
                    inventory=inventory,
                    pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                    reporting_func=reporting_func,
                )

            pi = results.pools.merge(results.classifiers)


            annual_carbon_stocks = pd.DataFrame(
                {
                    "Year": pi["timestep"],
                    "AGB": pi[self.AGB].sum(axis=1),
                    "BGB": pi[self.BGB].sum(axis=1),
                    "Deadwood": pi[self.deadwood].sum(axis=1),
                    "Litter": pi[self.litter].sum(axis=1),
                    "Soil": pi[self.soil].sum(axis=1),
                    "Total Ecosystem": pi[self.AGB
                                          + self.BGB
                                          + self.deadwood
                                          + self.litter
                                          + self.soil].sum(axis=1),

                }
            )

            annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
                ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
            ].sum()

            annual_carbon_stocks["Year"] = year_range

            return {"Stock": annual_carbon_stocks, "Raw": pi}


    def cbm_aggregate_scenario(self, sc):
        """
        Generate carbon stocks for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.

        Returns:
            dict: A dictionary containing the aggregated data.
                - "Stock": DataFrame containing annual carbon stocks.
                - "Structure": DataFrame containing age and area information.
                - "Raw": DataFrame containing raw data.
        """
        
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()
        forestry_end_year = self.forest_end_year
        path = self.path

        years = forestry_end_year - forest_baseline_year

        year_range = [
            year for year in range(forest_baseline_year, forestry_end_year +1)
        ]

        sit, classifiers, inventory = self.cbm_data_class.set_input_data_dir(sc, path)

        classifier_config = sit_cbm_factory.get_classifiers(
            sit.sit_data.classifiers, sit.sit_data.classifier_values
        )

        results, reporting_func = cbm_simulator.create_in_memory_reporting_func(
            classifier_map={
                x["id"]: x["value"] for x in classifier_config["classifier_values"]
            }
        )

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=reporting_func,
            )

        if self.gen_validation and sc != -1:
            ValidationData.get_disturbance_statistics(self.validation_path, rule_based_processor, years, sc)
            ValidationData.get_age_classes(self.validation_path, sit, sc)
            ValidationData.get_sit_events(self.validation_path, rule_based_processor, sc)
            ValidationData.merge_events(self.validation_path, sc)

        pi = results.pools.merge(results.classifiers)
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
        ].sum()

        annual_carbon_stocks["Year"] = year_range
        annual_carbon_stocks["Scenario"] = sc

        return {"Stock": annual_carbon_stocks, "Raw": pi}


    def libcbm_scenario_fluxes(self, sc):
        """
        Generate carbon Fluxes using the Libcbm method for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.

        Returns:
            dict: A dictionary containing the aggregated data.
                - "Stock": DataFrame containing annual carbon stocks.
                - "Structure": DataFrame containing age and area information.
                - "Raw": DataFrame containing raw data.
        """
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()
        forestry_end_year = self.forest_end_year
        path = self.path

        years = (forestry_end_year +1) - forest_baseline_year

        year_range = [
            year for year in range(forest_baseline_year -1, forestry_end_year +1)
        ]

        sit, classifiers, inventory = self.cbm_data_class.set_input_data_dir(sc, path)

        classifier_config = sit_cbm_factory.get_classifiers(
            sit.sit_data.classifiers, sit.sit_data.classifier_values
        )

        results, reporting_func = cbm_simulator.create_in_memory_reporting_func(
            classifier_map={
                x["id"]: x["value"] for x in classifier_config["classifier_values"]
            }
        )

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=reporting_func,
            )

        if self.gen_validation:
            ValidationData.get_disturbance_statistics(self.validation_path, rule_based_processor, years, sc)
            ValidationData.get_age_classes(self.validation_path, sit, sc)
            ValidationData.get_sit_events(self.validation_path, rule_based_processor, sc)
            ValidationData.merge_events(self.validation_path, sc)
            ValidationData.results_contents(self.validation_path, results, sc)

        flux_results = self.Flux_class.concatenated_fluxes_data(results).groupby(["TimeStep"]).sum()

        annual_process_fluxes = pd.DataFrame(
            {
                "Scenario": sc,
                "Timestep":flux_results.index,
                "Year": year_range,
                "AGB_delta": flux_results["DeltaBiomass_AG"],
                "BGB_delta": flux_results["DeltaBiomass_BG"],
                "DOM_delta": flux_results["DeltaDOM"],
                "Total Ecosystem_delta": flux_results["DeltaBiomass_AG"] + flux_results["DeltaBiomass_BG"] + flux_results["DeltaDOM"],

            }
        )
     

        return {"Stock": annual_process_fluxes, "Raw": flux_results}


    def cbm_scenario_fluxes(self, forest_data):
        """
        Calculate the carbon fluxes for each scenario in the given forest data.

        Args:
            forest_data (pd.DataFrame): DataFrame containing forest data.

        Returns:
            pd.DataFrame: DataFrame containing the calculated fluxes.
        """
        fluxes = pd.DataFrame(columns=forest_data.columns)

        for i in forest_data.index:
            if i > 0:
                fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i, "Year"])
                fluxes.loc[i - 1, "Scenario"] = int(forest_data.loc[i, "Scenario"])
                fluxes.loc[i - 1, "AGB"] = (
                    forest_data.loc[i, "AGB"] - forest_data.loc[i - 1, "AGB"]
                )
                fluxes.loc[i - 1, "BGB"] = (
                    forest_data.loc[i, "BGB"] - forest_data.loc[i - 1, "BGB"]
                )
                fluxes.loc[i - 1, "Deadwood"] = (
                    forest_data.loc[i, "Deadwood"] - forest_data.loc[i - 1, "Deadwood"]
                )
                fluxes.loc[i - 1, "Litter"] = (
                    forest_data.loc[i, "Litter"] - forest_data.loc[i - 1, "Litter"]
                )
                fluxes.loc[i - 1, "Soil"] = (
                    forest_data.loc[i, "Soil"] - forest_data.loc[i - 1, "Soil"]
                )
                fluxes.loc[i - 1, "Total Ecosystem"] = (
                    forest_data.loc[i, "Total Ecosystem"]
                    - forest_data.loc[i - 1, "Total Ecosystem"]
                )

        return fluxes