import cbm_runner.generated_input_data as input_data_path
import cbm_runner.baseline_input_conf as baseline_conf_path
from cbm_runner.cbm_data_factory import DataFactory
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.runner import Runner


import pandas as pd


class HistoricAfforRunner:
    """
    Orchestrates the running of CBM (Carbon Budget Model) for Irish historic afforestation.

    This class utilizes data factories and managers to set up and execute CBM simulations, generating outputs such as carbon stocks and fluxes for different scenarios. It also manages the creation of input data for these simulations.

    Attributes:
        path (str): Directory path for input data.
        baseline_conf_path (str): Directory path for baseline configuration data.
        cbm_data_class (DataFactory): Instance of the DataFactory class for CBM data preparation.
        data_manager_class (DataManager): Instance of the DataManager class for managing data and configurations.
        INDEX (list): List of unique scenario identifiers.
        forest_end_year (int): The end year of the forest simulation.
        runner_class (Runner): Instance of the Runner class for generating scenarios.

    Methods:
        generate_base_input_data(): Generates the baseline input data required for CBM simulations.
        generate_input_data(): Generates input data for various afforestation scenarios.
        afforestation_scenarios_structure(): Retrieves the structure data for each afforestation scenario.
        run_flux_scenarios(): Runs CBM simulations and calculates carbon flux data for different scenarios.
        run_aggregate_scenarios(): Runs and generates carbon stocks data from different CBM simulation scenarios.
    """
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforest_data,
        scenario_data,
    ):
        self.path = input_data_path.get_local_dir()
        self.baseline_conf_path = baseline_conf_path.get_local_dir()
        self.cbm_data_class = DataFactory(
            config_path, calibration_year, forest_end_year, afforest_data, scenario_data
        )
        self.data_manager_class = DataManager(calibration_year, config_path)

        self.INDEX = [int(i) for i in afforest_data.scenario.unique()]
        self.forest_end_year = forest_end_year
        
        self.runner_class = Runner(config_path,
        calibration_year,
        forest_end_year,
        afforest_data,
        scenario_data,
        gen_baseline=False,)



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
            forest_data = self.runner_class.cbm_aggregate_scenario(i)["Stock"]


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
            forest_data = self.runner_class.cbm_aggregate_scenario(i)["Stock"]

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data
