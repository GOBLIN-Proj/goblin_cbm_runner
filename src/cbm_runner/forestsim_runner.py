import cbm_runner.generated_input_data as input_data_path
import cbm_runner.baseline_input_conf as baseline_conf_path
from cbm_runner.forestsim_factory import ForestSimFactory
from cbm_runner.runner import Runner

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

    Attributes:
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
    """
    
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforest_data,
        afforest_data_annual,
        scenario_data,
    ):
        self.path = input_data_path.get_local_dir()
        self.baseline_conf_path = baseline_conf_path.get_local_dir()
        self.cbm_data_class = ForestSimFactory(
            config_path, calibration_year, forest_end_year, afforest_data, afforest_data_annual, scenario_data
        )

        self.cbm_runner_class = Runner(config_path,
            calibration_year,
            forest_end_year,
            afforest_data,
            scenario_data,)

        self.INDEX = [int(i) for i in afforest_data.scenario.unique()]


    def generate_base_input_data(self):
        """
        Generates the base input data for the CBM model.
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
        Generates the input data for each scenario in the CBM model.
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
        Runs the aggregate scenarios in the CBM model.

        Returns:
            The result of running the aggregate scenarios.
        """
        return self.cbm_runner_class.run_aggregate_scenarios()

    def run_flux_scenarios(self):
        """
        Runs the flux scenarios in the CBM model.

        Returns:
            The result of running the flux scenarios.
        """
        return self.cbm_runner_class.run_flux_scenarios()

