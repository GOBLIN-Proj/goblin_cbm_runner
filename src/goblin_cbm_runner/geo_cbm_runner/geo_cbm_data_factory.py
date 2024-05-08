"""
Geo Data Factory
=================

The ``DataFactory`` class is designed to generate and manage input data required for running Carbon Budget Model (CBM) simulations, 
focusing on geospatially specific catchment data for scenarios including afforestation, disturbances, and transitions. 
This class serves as a central hub for preparing, organizing, and storing various types of input data crucial for CBM simulation accuracy and efficiency.
"""
import pandas as pd
import math
import os
import shutil
import json
import itertools

from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.geo_cbm_runner.geo_create_json import CreateJSON
from goblin_cbm_runner.default_runner.yield_curves import YieldCurves
from goblin_cbm_runner.geo_cbm_runner.geo_inventory import Inventory
from goblin_cbm_runner.geo_cbm_runner.geo_disturbances import Disturbances
from goblin_cbm_runner.geo_cbm_runner.geo_transition import Transition
import goblin_cbm_runner.resource_manager.parser as parser


from libcbm.input.sit import sit_cbm_factory


class DataFactory:
    """
    Generates and manages input data required for running Carbon Budget Model (CBM) simulations, 
    focusing on geospatially specific catchment data for scenarios including afforestation, disturbances, 
    and transitions. This class serves as a central hub for preparing, organizing, and storing 
    various types of input data crucial for CBM simulation accuracy and efficiency.

    The DataFactory is designed to interact seamlessly with the GeoDataManager for data retrieval 
    and management, leveraging a suite of tools and modules for detailed environmental simulation 
    tasks. It automates the creation of necessary directories, configuration files, and CSV inputs 
    for classifiers, age classes, yield curves, inventories, disturbance events, disturbance types, 
    and transition rules tailored to specific simulation scenarios.

    Parameters:
    - config_path (str): Path to the simulation configuration file.
    - calibration_year (int): Year from which the simulation data is calibrated.
    - forest_end_year (int): Final year for the simulation period.
    - afforestation_data (dict): Data detailing afforestation activities within the simulation scope.
    - scenario_data (dict): Information defining various simulation scenarios.

    Attributes:
    - loader_class (Loader): Instance responsible for loading external resources or data.
    - data_manager_class (GeoDataManager): Manages retrieval and organization of geospatial data.
    - json_creator_class (CreateJSON): Constructs JSON files for CBM configuration.
    - inventory_class (Inventory): Prepares inventory data for simulations.
    - disturbance_class (Disturbances): Manages data related to forest disturbances.
    - transition_class (Transition): Handles transition rule data for forest change modeling.
    - afforestation_data (dict): Stores afforestation data for use in simulations.

    Methods:
    - set_input_data_dir(sc, path): Configures the directory path for scenario-specific input data.
    - set_baseline_input_data_dir(path): Establishes the directory path for baseline simulation input data.
    - make_data_dirs(scenarios, path): Generates directories for each specified simulation scenario.
    - clean_data_dir(path): Removes all data within a specified directory, preparing it for fresh data.
    - clean_baseline_data_dir(path): Clears the baseline data directory of all files except essential ones.
    - make_config_json(scenario, path): Creates a JSON file for CBM configuration based on a given scenario.
    - make_classifiers(scenario, path): Generates a CSV file detailing classifiers relevant to the scenario.
    - make_age_classes(scenario, path): Produces a CSV file outlining age classes for forest simulation.
    - make_yield_curves(scenario, path): Compiles yield curve data into a CSV for simulation input.
    - make_inventory(scenario, path): Prepares and saves inventory data as a CSV file for a given scenario.
    - make_disturbance_events(scenario, path): Constructs a CSV file detailing disturbance events per scenario.
    - make_disturbance_type(scenario, path): Creates a CSV file defining types of disturbances for modeling.
    - make_transition_rules(scenario, path): Generates a CSV file with transition rules for forest dynamics.
    """
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        scenario_data,
    ):
        self.loader_class = Loader()
        self.data_manager_class = GeoDataManager(calibration_year=calibration_year, config_file=config_path)
        self.json_creator_class = CreateJSON(config_path)
        self.inventory_class = Inventory(
            calibration_year, config_path, scenario_data, afforestation_data
        )
        self.disturbance_class = Disturbances(
            config_path,
            calibration_year,
            forest_end_year,
            afforestation_data,
            scenario_data,
        )
        self.transition_class = Transition(calibration_year, config_path)
        self.afforestation_data = afforestation_data


    def set_input_data_dir(self, sc, path, db_path):
        """
        Sets the input data directory for a scenario, initializes the CBM simulation data.

        This methods loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs 
            * Classifiers: Descriptions of forest stands (species, soil type, etc.)
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.

        Returns:
            tuple: A tuple containing the following:
                * SIT object:  The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, str(sc), "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory

    def set_baseline_input_data_dir(self, path, db_path):
        """
        Sets the input data directory for the baseline, initializes the CBM simulation data.

        This methods loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs 
            * Classifiers: Descriptions of forest stands (species, soil type, etc.)
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.

        Returns:
            tuple: A tuple containing the following:
                * SIT object:  The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory
    
    def set_spinup_baseline_input_data_dir(self, path, db_path):
        """
        Sets the input data directory for the baseline, initializes the CBM simulation data.

        This methods loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs 
            * Classifiers: Descriptions of forest stands (species, soil type, etc.)
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.

        Returns:
            tuple: A tuple containing the following:
                * SIT object:  The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, "spinup_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory
    

    def set_input_data_dir(self, sc, path, db_path):
        """
        Sets the input data directory for a scenario, initializes the CBM simulation data.

        This methods loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs 
            * Classifiers: Descriptions of forest stands (species, soil type, etc.)
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.

        Returns:
            tuple: A tuple containing the following:
                * SIT object:  The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, str(sc), "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory

    def set_baseline_input_data_dir(self, path, db_path):
        """
        Sets the input data directory for the baseline, initializes the CBM simulation data.

        This methods loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs 
            * Classifiers: Descriptions of forest stands (species, soil type, etc.)
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.

        Returns:
            tuple: A tuple containing the following:
                * SIT object:  The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory
    

    def make_data_dirs(self, scenarios, path):
        """
        Creates data directories.

        Args:
            scenarios (list): A list of scenario numbers.
            path (str): The path to the data directory.
        """
        for sc in scenarios:
            os.mkdir(os.path.join(path, str(sc)))

    def clean_data_dir(self, path):
        """
        Cleans the data directory.

        Args:
            path (str): The path to the data directory.
        """
        for directory in os.listdir(path):
            d = os.path.join(path, directory)
            if not os.path.isfile(d):
                shutil.rmtree(d)

    def clean_baseline_data_dir(self, path):
        """
        Cleans the baseline data directory.

        Args:
            path (str): The path to the baseline data directory.
        """
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) and filename != "__init__.py":
                os.remove(file_path)


    def make_config_json(self, scenario, path):
        """
        Creates the configuration JSON file.

        Args:
            scenario (int): The scenario number.
            path (str): The path to the output directory.
        """
        dictionary = self.json_creator_class.populate_template(scenario)

        file = "sit_config.json"

        spinup_dictionary = self.json_creator_class.populate_spinup_template()

        file2 = "spinup_config.json"

        # Writing to outfile
        if scenario is not None:
            with open(os.path.join(path, str(scenario), file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)
        else:
            with open(os.path.join(path, file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)

            with open(os.path.join(path, file2), "w") as outfile2:
                json.dump(spinup_dictionary, outfile2, indent=4)

    def make_classifiers(self, scenario, path):
        """
        Generates a dataframe of classifiers and saves it as a CSV file.

        Parameters:
        - scenario (str): The scenario name. If provided, classifiers for the scenario will be generated.
        - path (str): The path where the CSV file will be saved.

        Returns:
        None
        """
        
        if scenario is not None:
            classifiers = self.data_manager_class.get_classifiers()["Scenario"]
        else:
            classifiers = self.data_manager_class.get_classifiers()["Baseline"]

        cols = ["classifier_id", "name", "description"]
        classifier_df = pd.DataFrame(columns=cols)

        for num, classifier in enumerate(classifiers.keys()):
            row = pd.DataFrame(
                [dict(zip(cols, [(num + 1), "_CLASSIFIER", classifier]))]
            )
            classifier_df = pd.concat([classifier_df, row])

            for key, value in classifiers[classifier].items():
                name = key
                description = value

                row = pd.DataFrame([dict(zip(cols, [(num + 1), name, description]))])
                classifier_df = pd.concat([classifier_df, row])

        if scenario is not None:
            classifier_df.to_csv(
                os.path.join(path, str(scenario), "classifiers.csv"), index=False
            )
        else:
            classifier_df.to_csv(os.path.join(path, "classifiers.csv"), index=False)


    def make_age_classes(self, scenario, path):
        """
        Creates age classes DataFrame and saves it as a CSV file.

        Args:
            scenario (str): The scenario name. If provided, the CSV file will be saved in a subdirectory with the scenario name.
            path (str): The path where the CSV file will be saved.

        Returns:
            None
        """
        
        classifiers = self.data_manager_class.config_data["Classifiers"]

        age = parser.get_age_classifier(classifiers)

        cols = ["id", "size"]

        age_classes_df = pd.DataFrame(columns=cols)

        age_classes_df["id"] = age.keys()
        age_classes_df["size"] = age.values()

        if scenario is not None:
            age_classes_df.to_csv(
                os.path.join(path, str(scenario), "age_classes.csv"), index=False
            )
        else:
            age_classes_df.to_csv(os.path.join(path, "age_classes.csv"), index=False)


    def gen_yield_dataframe(self, classifiers, yield_df):

        shared_classifiers = self.data_manager_class.config_data["Classifiers"]

        name_dict = self.data_manager_class.get_yield_name_dict()
        afforestation_yield_name_dict = (
            self.data_manager_class.get_afforestation_yield_name_dict()
        )

        max_age = shared_classifiers["age_classes"]["max_age"]
        age_interval = shared_classifiers["age_classes"]["age_interval"]

        cols = parser.get_classifier_list(classifiers)

        age_range = list(range(0, max_age + age_interval, age_interval))

        vol_cols = [f"Vol{x}" for x in range(len(age_range))]

        vol_dict = dict(zip(vol_cols, age_range))

        cols = cols + vol_cols
        growth_df = pd.DataFrame(columns=cols)

        count = 0

        for species in classifiers["Species"].keys():
            forest_keys = list(classifiers["Forest type"].keys())
            soil_keys = list(classifiers["Soil classes"].keys())
            yield_keys = list(classifiers["Yield classes"].keys())

            for forest_type, soil, yield_class in itertools.product(
                forest_keys, soil_keys, yield_keys
            ):
                for vol in vol_cols:
                    if (
                        forest_type == "A"
                        and species in afforestation_yield_name_dict.keys()
                        and yield_class in afforestation_yield_name_dict[species]
                    ):
                        growth_df.loc[count, "Classifier1"] = species
                        growth_df.loc[count, "Classifier2"] = forest_type
                        growth_df.loc[count, "Classifier3"] = soil
                        growth_df.loc[count, "Classifier4"] = yield_class
                        growth_df.loc[count, "LeadSpecies"] = species
                        growth_df.loc[count, vol] = 0

                    else:
                        if (
                            forest_type == "L"
                            and species in name_dict.keys()
                            and yield_class in name_dict[species].keys()
                        ):
                            growth_df.loc[count, "Classifier1"] = species
                            growth_df.loc[count, "Classifier2"] = forest_type
                            growth_df.loc[count, "Classifier3"] = soil
                            growth_df.loc[count, "Classifier4"] = yield_class
                            growth_df.loc[count, "LeadSpecies"] = species

                            if vol == "Vol0":
                                growth_df.loc[count, vol] = 0
                            else:
                                growth_df.loc[count, vol] = yield_df.loc[
                                    name_dict[species][yield_class],
                                    vol_dict[vol],
                                ].item()

                count += 1
        return growth_df

    def make_yield_curves(self, scenario, path):
        """
        Creates the yield curves CSV file.

        Args:
            scenario (int): The scenario number.
            path (str): The path to the output directory.

        Returns:
            None
        """
        yield_df = YieldCurves.yield_table_generater_method3()

        standing_vol_yield_df = YieldCurves.standing_vol_yield_table_generater_method()


        if scenario is not None:
            classifiers = self.data_manager_class.get_classifiers()["Scenario"]
            self.gen_yield_dataframe(classifiers, yield_df).to_csv(
                os.path.join(path, str(scenario), "growth.csv"), index=False
            )

        else:
            classifiers = self.data_manager_class.get_classifiers()["Baseline"]

            self.gen_yield_dataframe(classifiers, yield_df).to_csv(
                os.path.join(path, "growth.csv"), index=False
            )

            self.gen_yield_dataframe(classifiers, standing_vol_yield_df).to_csv(
                os.path.join(path, "standing_vol.csv"), index=False
            )


    def make_inventory(self, scenario, path):
        """
        Create an inventory DataFrame based on the given scenario and path.

        Args:
            scenario (str): The scenario for which the inventory is created.
            path (str): The path where the inventory file will be saved.

        Returns:
            pandas.DataFrame: The created inventory DataFrame.

        Raises:
            None

        """
        inventory_df = self.inventory_class.make_inventory_structure(scenario, path)

        if scenario is not None:
            inventory_df = self.inventory_class.afforestation_inventory(
                scenario, inventory_df
            )
            inventory_df.to_csv(
                os.path.join(path, str(scenario), "inventory.csv"), index=False
            )
        else:
            inventory_df = self.inventory_class.inventory_iterator(
                scenario, inventory_df
            )
            inventory_df.to_csv(os.path.join(path, "inventory.csv"), index=False)

    def make_disturbance_events(self, scenario, path):
        """
        Generate disturbance events data and save it as a CSV file.

        Args:
            scenario (str or None): The scenario name. If None, baseline forest data will be generated.
            path (str): The path to save the disturbance events CSV file.

        Returns:
            None
        """
        if scenario is not None:
            disturbance_events = self.disturbance_class.fill_scenario_data(scenario)
            disturbance_events.to_csv(
                os.path.join(path, str(scenario), "disturbance_events.csv"), index=False
            )
        else:
            disturbance_events = self.disturbance_class.fill_baseline_forest()
            disturbance_events.to_csv(
                os.path.join(path, "disturbance_events.csv"), index=False
            )

    def make_disturbance_type(self, scenario, path):
        """
        Creates a disturbance type CSV file based on the given scenario and saves it to the specified path.

        Parameters:
        - scenario (str): The scenario for which the disturbance type CSV file is created. If None, the baseline disturbance types are used.
        - path (str): The path where the disturbance type CSV file is saved.

        Returns:
        None
        """
        
        if scenario != None:
            classifiers = self.data_manager_class.get_disturbances_config()["Scenario"]
        else:
            classifiers = self.data_manager_class.get_disturbances_config()["Baseline"]

        cols = ["id", "name"]
        disturbance_type_df = pd.DataFrame(columns=cols)

        disturbance_dataframe = self.loader_class.disturbance_type()

        for dist in classifiers:
            id = dist
            description = disturbance_dataframe.loc[
                (disturbance_dataframe["Disturbance"] == dist), "Description"
            ].item()

            row = pd.DataFrame([dict(zip(cols, [id, description]))])
            disturbance_type_df = pd.concat([disturbance_type_df, row])

        if scenario is not None:
            disturbance_type_df.to_csv(
                os.path.join(path, str(scenario), "disturbance_types.csv"),
                index=False,
            )
        else:
            disturbance_type_df.to_csv(
                os.path.join(path, "disturbance_types.csv"),
                index=False,
            )

    def make_transition_rules(self, scenario, path):
        """
        Generate transition rules based on the given scenario and save them to a CSV file.

        Args:
            scenario (str or None): The scenario for which the transition rules are generated.
                If None, the transition rules are generated for all scenarios.
            path (str): The path where the CSV file should be saved.

        Returns:
            None
        """
        transition_df = self.transition_class.make_transition_rules_structure(scenario)

        if scenario is not None:
            transition_df.to_csv(
                os.path.join(path, str(scenario), "transitions.csv"), index=False
            )
        else:
            transition_df.to_csv(os.path.join(path, "transitions.csv"), index=False)
