"""
Forest Sim Runner
=================

The ForestSimRunner class is responsible for generating input data and running scenarios in the CBM model.

"""
from goblin_cbm_runner.forest_sim.forestsim_factory import ForestSimFactory
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
from goblin_cbm_runner.resource_manager.paths import Paths
from goblin_cbm_runner.cbm.cbm_methods import CBMSim
import pandas as pd


class ForestSimRunner:
    """
    The ForestSimRunner class is responsible for generating input data and running scenarios in the CBM model.
    
    This class is used when annual afforesation has been specified for each year.

    Args:
        config_path (str): The path to the CBM configuration file.
        calibration_year (int): The year used for calibration.
        forest_end_year (int): The final year of the simulation.
        afforest_data (AfforestData): The afforestation data.
        afforest_data_annual (AfforestDataAnnual): The annual afforestation data.
        scenario_data (ScenarioData): The scenario data.
        gen_baseline (bool): A flag to generate the baseline data.
        gen_validation (bool): A flag to generate the validation data.

    Attributes:
        paths_class (Paths): The instance of the Paths class.
        gen_validation (bool): A flag to generate the validation data.
        validation_path (str): The path to the validation directory.
        path (str): The path to the local directory.
        baseline_conf_path (str): The path to the baseline configuration directory.
        cbm_data_class (ForestSimFactory): The instance of the ForestSimFactory class.
        cbm_runner_class (Runner): The instance of the Runner class.
        INDEX (list): The list of unique scenario indices.

    Methods:
        generate_base_input_data(): Generates the base input data for the CBM model.
        generate_input_data(): Generates the input data for each scenario in the CBM model.
        run_aggregate_scenarios(): Runs the aggregate scenarios in the CBM model.
        run_flux_scenarios(): Runs the flux scenarios in the CBM model.

    Note:
        An external path can be specified to generate the validation data.
    """
    
    def __init__(
        self,
        config_path,
        calibration_year,
        afforest_data,
        afforest_data_annual,
        scenario_data,
    ):
        
        self.paths_class = Paths(None, gen_baseline=True)
        self.paths_class.setup_forest_runner_paths(None)
        
        self.defaults_db = self.paths_class.get_aidb_path()

        self.path = self.paths_class.get_generated_input_data_path()
        self.baseline_conf_path = self.paths_class.get_baseline_conf_path()

        self.sc_fetcher = ScenarioDataFetcher(scenario_data)
        self.forest_end_year = self.sc_fetcher.get_afforestation_end_year()

        self.data_manager_class = DataManager(calibration_year=calibration_year, config_file=config_path)

        self.cbm_data_class = ForestSimFactory(
            config_path, calibration_year, self.forest_end_year, afforest_data, afforest_data_annual, scenario_data
        )


        self.INDEX = self.sc_fetcher.get_afforest_scenario_index()
        self.SIM_class = CBMSim()

        self.scenario_years = self.data_manager_class.get_scenario_years(self.forest_end_year)

        self.scenario_year_range = self.data_manager_class.get_scenario_years_range(self.forest_end_year)

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
                                                                      self.scenario_years, 
                                                                      self.scenario_year_range, 
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
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil","Harvest", "Total Ecosystem"]
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
                                                                      self.scenario_years, 
                                                                      self.scenario_year_range, 
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
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil","Harvest", "Total Ecosystem"]
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