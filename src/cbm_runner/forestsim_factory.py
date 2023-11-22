from cbm_runner.cbm_data_factory import DataFactory
from cbm_runner.forestsim_disturbances import ForestSimDistrubances
import os 

class ForestSimFactory:
    """
    A factory class for creating and managing forest simulation data in a CBM context.

    This class is used when annual afforesation has been specified for each year. 

    This class serves as a central point for managing the creation and organization of various data files 
    necessary for running forest simulations, including configuration files, classifiers, age classes, 
    yield curves, disturbance types, transition rules, inventory, and disturbance events.

    Args:
        config_path (str): The path to the configuration file.
        calibration_year (int): The year used for calibration.
        forest_end_year (int): The final year of the forest simulation.
        afforestation_data (pd.DataFrame): The afforestation data.
        afforest_data_annual (pd.DataFrame): The annual afforestation data.
        scenario_data (pd.DataFrame): The scenario data.

    Attributes:
        DataFactory (DataFactory): An instance of the DataFactory class.
        disturbance_class (ForestSimDistrubances): An instance of the ForestSimDistrubances class.

    Methods:
        set_input_data_dir(sc, path): Set the input data directory for a specific scenario.
        set_baseline_input_data_dir(path): Set the input data directory for the baseline scenario.
        make_data_dirs(scenarios, path): Create data directories for specified scenarios.
        clean_data_dir(path): Clean the data directory.
        clean_baseline_data_dir(path): Clean the baseline data directory.
        make_config_json(scenario, path): Create configuration JSON for a specific scenario.
        make_classifiers(scenario, path): Create classifiers file for a specific scenario.
        make_age_classes(scenario, path): Create age classes file for a specific scenario.
        make_yield_curves(scenario, path): Create yield curves file for a specific scenario.
        make_disturbance_type(scenario, path): Create disturbance type file for a specific scenario.
        make_transition_rules(scenario, path): Create transition rules file for a specific scenario.
        make_inventory(scenario, path): Create inventory file for a specific scenario.
        make_disturbance_events(scenario, path): Create disturbance events file for a specific scenario.
    """

    def __init__(self, config_path, calibration_year, forest_end_year, afforestation_data, afforest_data_annual, scenario_data):
        self.DataFactory = DataFactory(config_path, calibration_year, forest_end_year, afforestation_data, scenario_data)
        self.disturbance_class = ForestSimDistrubances(config_path, calibration_year, forest_end_year, afforestation_data, afforest_data_annual, scenario_data)

    def set_input_data_dir(self, sc, path):
        """
        Set the input data directory for a specific scenario.

        Args:
            sc (str): The scenario identifier.
            path (str): The path to the input data directory.

        """
        self.DataFactory.set_input_data_dir(sc, path)

    def set_baseline_input_data_dir(self, path):
        """
        Set the input data directory for the baseline scenario.

        Args:
            path (str): The path to the input data directory.

        """
        self.DataFactory.set_baseline_input_data_dir(path)

    def make_data_dirs(self, scenarios, path):
        """
        Create data directories for the specified scenarios.

        Args:
            scenarios (list): A list of scenario identifiers.
            path (str): The path to the data directories.

        """
        self.DataFactory.make_data_dirs(scenarios, path)

    def clean_data_dir(self, path):
        """
        Clean the data directory.

        Args:
            path (str): The path to the data directory.

        """
        self.DataFactory.clean_data_dir(path)

    def clean_baseline_data_dir(self, path):
        """
        Clean the baseline data directory.

        Args:
            path (str): The path to the baseline data directory.

        """
        self.DataFactory.clean_baseline_data_dir(path)

    def make_config_json(self, scenario, path):
        """
        Create the configuration JSON file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the configuration JSON file.

        """
        self.DataFactory.make_config_json(scenario, path)

    def make_classifiers(self, scenario, path):
        """
        Create the classifiers file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the classifiers file.

        """
        self.DataFactory.make_classifiers(scenario, path)

    def make_age_classes(self, scenario, path):
        """
        Create the age classes file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the age classes file.

        """
        self.DataFactory.make_age_classes(scenario, path)

    def make_yield_curves(self, scenario, path):
        """
        Create the yield curves file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the yield curves file.

        """
        self.DataFactory.make_yield_curves(scenario, path)

    def make_disturbance_type(self, scenario, path):
        """
        Create the disturbance type file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the disturbance type file.

        """
        self.DataFactory.make_disturbance_type(scenario, path)

    def make_transition_rules(self, scenario, path):
        """
        Create the transition rules file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the transition rules file.

        """
        self.DataFactory.make_transition_rules(scenario, path)

    def make_inventory(self, scenario, path):
        """
        Create the inventory file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the inventory file.

        """
        self.DataFactory.make_inventory(scenario, path)

    def make_disturbance_events(self, scenario, path):
        """
        Create the disturbance events file for a specific scenario.

        Args:
            scenario (str): The scenario identifier.
            path (str): The path to save the disturbance events file.

        """
        if scenario is not None:
            disturbance_events = self.disturbance_class.fill_scenario_data(scenario)
            disturbance_events.to_csv(
                os.path.join(path, str(scenario), "disturbance_events.csv"), index=False
            )
        else:
            disturbance_events = self.disturbance_class.fill_baseline_forest()
            disturbance_events.to_csv(
                os.path.join(path, "disturbance_events.csv"), index=False)
    

    

