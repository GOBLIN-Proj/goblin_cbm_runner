"""
Data Factory Module
==============
This module contains the DataFactory class, which is used to create and manage input data for CBM simulations.

**Key Features**

* **Dynamic Data Generation:** Creates and organizes input files (configuration files, classifiers, age classes, yield curves, inventories, disturbance events/types, and transition rules) for both baseline and specific scenarios.
* **Flexibility:** Facilitates customization of CBM simulations by allowing modification of input data.
* **Data Integrity:** Ensures consistency and accuracy of generated CBM input data.

"""

import pandas as pd
import os
import shutil
import json
import itertools

from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.create_json import CreateJSON
from goblin_cbm_runner.cbm.data_processing.default_processing.yield_curves import YieldCurves
from goblin_cbm_runner.cbm.data_processing.default_processing.SC_inventory import SCInventory
from goblin_cbm_runner.cbm.data_processing.default_processing.SC_disturbances import SCDisturbances
from goblin_cbm_runner.cbm.data_processing.default_processing.transition import Transition
import goblin_cbm_runner.resource_manager.parser as parser


from libcbm.input.sit import sit_cbm_factory


class DataFactory:
    """
    A class that represents a data factory for creating and managing input data for CBM simulations.

    Attributes:
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (DataManager): An instance of the DataManager class.
        json_creator_class (CreateJSON): An instance of the CreateJSON class.
        SC_inventory_class (SCInventory): An instance of the SCInventory class.
        SC_disturbance_class (SCDisturbances): An instance of the SCDisturbances class.
        transition_class (Transition): An instance of the Transition class.
        afforestation_data (DataFrame): Detailed data of afforestation activities per scenario.
        management_intensity (DataFrame): Data on forest management intensity.

    Methods:
        set_input_data_dir(sc, path, db_path): Sets the input data directory for a scenario, loads SIT, classifiers, and inventory.
        set_baseline_input_data_dir(path, db_path): Sets the baseline input data directory, loads SIT, classifiers, and inventory.
        set_spinup_baseline_input_data_dir(path, db_path): Sets the spinup baseline input data directory, loads SIT, classifiers, and inventory.
        make_data_dirs(scenarios, path): Creates data directories for specified scenarios.
        clean_data_dir(path): Removes existing data from a directory.
        clean_baseline_data_dir(path): Removes existing data from the baseline directory.
        make_config_json(scenario, path): Creates a configuration JSON file.
        make_classifiers(scenario, path): Creates a classifiers CSV file.
        make_age_classes(scenario, path): Creates an age classes CSV file.
        make_yield_curves(scenario, path): Creates a yield curves CSV file.
        make_inventory(scenario, path): Creates an inventory CSV file.
        make_disturbance_events(scenario, path): Creates a disturbance events CSV file.
        make_disturbance_type(scenario, path): Creates a disturbance type CSV file.
        make_transition_rules(scenario, path): Creates a transition rules CSV file.
        make_base_age_classes(path): Creates the baseline age classes CSV file.
        make_base_classifiers(path): Creates the baseline classifiers CSV file.
        make_base_yield_curves(path): Creates the baseline yield curves CSV files.
        make_base_inventory(path): Creates the baseline inventory CSV file.
        make_base_disturbance_events(path): Creates the baseline disturbance events CSV file.
        make_base_disturbance_type(path): Creates the baseline disturbance type CSV file.
        make_base_transition_rules(path): Creates the baseline transition rules CSV file.
        make_FM_age_classes(path): Creates age classes CSV file for managed forest.
        make_FM_classifiers(path): Creates classifiers CSV file for managed forest.
        make_FM_yield_curves(path): Creates yield curves CSV file for managed forest.
        make_FM_inventory(path): Creates inventory CSV file for managed forest.
        make_FM_disturbance_events(path): Creates disturbance events CSV file for managed forest.
        make_FM_disturbance_type(path): Creates disturbance type CSV file for managed forest.
        make_FM_transition_rules(path): Creates transition rules CSV file for managed forest.
        make_AF_age_classes(path): Creates age classes CSV file for historic afforestation.
        make_AF_classifiers(path): Creates classifiers CSV file for historic afforestation.
        make_AF_yield_curves(path): Creates yield curves CSV file for historic afforestation.
        make_AF_inventory(path): Creates inventory CSV file for historic afforestation.
        make_AF_disturbance_events(path): Creates disturbance events CSV file for historic afforestation.
        make_AF_disturbance_type(path): Creates disturbance type CSV file for historic afforestation.
        make_AF_transition_rules(path): Creates transition rules CSV file for historic afforestation.
    """
    def __init__(
        self,
        data_manager,
    ):
        self.loader_class = Loader()
        self.data_manager_class = data_manager

        self.json_creator_class = CreateJSON(data_manager)
        self.SC_inventory_class = SCInventory(data_manager)

        self.SC_disturbance_class = SCDisturbances(data_manager)   
        self.transition_class = Transition(data_manager)
        
        self.afforestation_data =self.data_manager_class.get_afforest_data()

        self.management_intensity = self.data_manager_class.get_forest_management_intensity()


    def set_input_data_dir(self, sc, path, db_path):
        """
        Sets the input data directory for a scenario, initializes the CBM simulation data.

        This method loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs.
            * Classifiers: Descriptions of forest stands (species, soil type, etc.).
            * Inventory: Data on the initial forest composition.

        Args:
            sc (int): The scenario number.
            path (str): The path to the input data directory.
            db_path (str): The path to the database.

        Returns:
            tuple: A tuple containing the following:
                * SIT object: The loaded SIT configuration.
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

        This method loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs.
            * Classifiers: Descriptions of forest stands (species, soil type, etc.).
            * Inventory: Data on the initial forest composition.

        Args:
            path (str): The path to the input data directory.
            db_path (str): The path to the database.

        Returns:
            tuple: A tuple containing the following:
                * SIT object: The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory
    
    def set_spinup_baseline_input_data_dir(self, path, db_path):
        """
        Sets the input data directory for the spinup baseline, initializes the CBM simulation data.

        This method loads the following using the CBM's Standard Import Tool (SIT):
            * SIT configuration: Settings that govern how the CBM simulation runs.
            * Classifiers: Descriptions of forest stands (species, soil type, etc.).
            * Inventory: Data on the initial forest composition.

        Args:
            path (str): The path to the input data directory.
            db_path (str): The path to the database.

        Returns:
            tuple: A tuple containing the following:
                * SIT object: The loaded SIT configuration.
                * classifiers (DataFrame): Classifiers for the forest stands.
                * inventory (DataFrame): The forest inventory data.
        """
        sit_config_path = os.path.join(path, "spinup_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory

    def make_data_dirs(self, scenarios, path):
        """
        Creates data directories for specified scenarios.

        Args:
            scenarios (list): A list of scenario numbers.
            path (str): The path to the data directory.
        """
        for sc in scenarios:
            os.mkdir(os.path.join(path, str(sc)))

    def clean_data_dir(self, path):
        """
        Removes existing data from a directory.

        Args:
            path (str): The path to the data directory.
        """
        for directory in os.listdir(path):
            d = os.path.join(path, directory)
            if not os.path.isfile(d):
                shutil.rmtree(d)

    def clean_baseline_data_dir(self, path):
        """
        Removes existing data from the baseline directory.

        Args:
            path (str): The path to the baseline data directory.
        """
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) and filename != "__init__.py":
                os.remove(file_path)


    def make_config_json(self, scenario, path):
        """
        Creates a configuration JSON file.

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
        Creates a classifiers CSV file.

        Args:
            scenario (str): The scenario name. If provided, classifiers for the scenario will be generated.
            path (str): The path where the CSV file will be saved.
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
        Creates an age classes CSV file.

        Args:
            scenario (str): The scenario name. If provided, the CSV file will be saved in a subdirectory with the scenario name.
            path (str): The path where the CSV file will be saved.
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


    def make_yield_curves(self, scenario, path):
        """
        Creates a yield curves CSV file.

        Args:
            scenario (int): The scenario number.
            path (str): The path to the output directory.
        """
        yield_df = YieldCurves.yield_table_generater_method3()

        shared_classifiers = self.data_manager_class.config_data["Classifiers"]

        if scenario is not None:
            classifiers = self.data_manager_class.get_classifiers()["Scenario"]

        else:
            classifiers = self.data_manager_class.get_classifiers()["Baseline"]

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

        if scenario is not None:
            growth_df.to_csv(
                os.path.join(path, str(scenario), "growth.csv"), index=False
            )
        else:
            growth_df.to_csv(os.path.join(path, "growth.csv"), index=False)


    def make_inventory(self, scenario, path):
        """
        Creates an inventory CSV file.

        Args:
            scenario (str): The scenario for which the inventory is created.
            path (str): The path where the inventory file will be saved.
        """
        if scenario == -1:
            self.make_AF_inventory(os.path.join(path, str(scenario)))
           
        else:

            inventory_df = self.SC_inventory_class.scenario_inventory(
                scenario, path
            )
            inventory_df.to_csv(os.path.join(path,str(scenario), "inventory.csv"), index=False)


    def make_disturbance_events(self, scenario, path):
        """
        Creates a disturbance events CSV file.

        Args:
            scenario (str or None): The scenario name. If None, baseline forest data will be generated.
            path (str): The path to save the disturbance events CSV file.
        """
        if scenario is None:
            self.make_AF_disturbance_events(path)

        elif scenario == -1:
            self.make_AF_disturbance_events(os.path.join(path, str(scenario)))
        else: 
            disturbance_events = self.SC_disturbance_class.fill_scenario_data(scenario)
            disturbance_events.to_csv(
                os.path.join(path, str(scenario), "disturbance_events.csv"), index=False
            )


    def make_disturbance_type(self, scenario, path):
        """
        Creates a disturbance type CSV file.

        Args:
            scenario (str): The scenario for which the disturbance type CSV file is created. If None, the baseline disturbance types are used.
            path (str): The path where the disturbance type CSV file is saved.
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
        Creates a transition rules CSV file.

        Args:
            scenario (str or None): The scenario for which the transition rules are generated.
            path (str): The path where the CSV file should be saved.
        """
        transition_df = self.transition_class.make_transition_rules_structure(scenario)

        if scenario is not None:
            transition_df.to_csv(
                os.path.join(path, str(scenario), "transitions.csv"), index=False
            )
        else:
            transition_df.to_csv(os.path.join(path, "transitions.csv"), index=False)



    def make_FM_age_classes(self, path):
        """
        Creates age classes CSV file for managed forest.

        Args:
            path (str): The path where the CSV file will be saved.
        """
    
        self.loader_class.FM_age_class().to_csv(
            os.path.join(path, "age_classes.csv"), index=False
        )


    def make_FM_classifiers(self, path):
        """
        Creates classifiers CSV file for managed forest.

        Args:
            path (str): The path where the CSV file will be saved.
        """
        self.loader_class.FM_classifiers().to_csv(
                os.path.join(path, "classifiers.csv"), index=False
            )
        
    def make_FM_yield_curves(self, path):
        """
        Creates yield curves CSV file for managed forest.

        Args:
            path (str): The path to the output directory.
        """
        
        self.loader_class.FM_growth_curves().to_csv(
            os.path.join(path, "growth.csv"), index=False
        )

        self.loader_class.FM_standing_volume().to_csv(
            os.path.join(path, "standing_vol.csv"), index=False
        )

    def make_FM_inventory(self, path):
        """
        Creates inventory CSV file for managed forest.

        Args:
            path (str): The path to the output directory.
        """
            
        self.loader_class.FM_inventory().to_csv(
            os.path.join(path, "inventory.csv"), index=False
        )


    def make_FM_disturbance_events(self, path):
        """
        Creates disturbance events CSV file for managed forest.

        Args:
            path (str): The path to the output directory.
        """

        self.loader_class.FM_disturbances_time_series(intensity=self.management_intensity).to_csv(
            os.path.join(path, "disturbance_events.csv"), index=False
        )

    def make_FM_disturbance_type(self, path):
        """
        Creates disturbance type CSV file for managed forest.

        Args:
            path (str): The path to the output directory.
        """
            
        self.loader_class.FM_disturbance_types().to_csv(
                os.path.join(path, "disturbance_types.csv"), index=False
            )
        
    def make_FM_transition_rules(self, path):
        """
        Creates transition rules CSV file for managed forest.

        Args:
            path (str): The path to the output directory.
        """
        
        transition_df=self.loader_class.FM_transition()

        # Identify columns starting with "Classifier"
        classifier_columns = [col for col in transition_df.columns if col.startswith('Classifier')]

        # Identify the index of 'DistType' to know where to insert the duplicated classifiers
        insert_index = transition_df.columns.get_loc('DistType') + 1  # +1 to insert after 'DistType'

        # Duplicate classifier columns
        duplicated_classifiers = transition_df[classifier_columns].copy()

        # Create new DataFrame with the required structure
        new_transition_df = pd.concat([
            transition_df.iloc[:, :insert_index],  # Columns before and including 'DistType'
            duplicated_classifiers,       # Duplicated classifier columns
            transition_df.iloc[:, insert_index:]   # Columns from 'DistType' onwards (excluding since it's included in the first part)
        ], axis=1)

        new_transition_df.to_csv(os.path.join(path, "transitions.csv"), index=False)

    def make_AF_age_classes(self, path):
        """
        Creates age classes CSV file for historic afforestation.

        Args:
            path (str): The path where the CSV file will be saved.
        """
    
        self.loader_class.AF_age_class().to_csv(
            os.path.join(path, "age_classes.csv"), index=False
        )


    def make_AF_classifiers(self, path):
        """
        Creates classifiers CSV file for historic afforestation.

        Args:
            path (str): The path where the CSV file will be saved.
        """
        self.loader_class.AF_classifiers().to_csv(
                os.path.join(path, "classifiers.csv"), index=False
            )
        
    def make_AF_yield_curves(self, path):
        """
        Creates yield curves CSV file for historic afforestation.

        Args:
            path (str): The path to the output directory.
        """
        
        self.loader_class.AF_growth_curves().to_csv(
            os.path.join(path, "growth.csv"), index=False
        )

        self.loader_class.AF_standing_volume().to_csv(
            os.path.join(path, "standing_vol.csv"), index=False
        )

    def make_AF_inventory(self, path):
        """
        Creates inventory CSV file for historic afforestation.

        Args:
            path (str): The path to the output directory.
        """
            
        self.loader_class.AF_inventory().to_csv(
            os.path.join(path, "inventory.csv"), index=False
        )


    def make_AF_disturbance_events(self, path):
        """
        Creates disturbance events CSV file for historic afforestation.

        Args:
            path (str): The path to the output directory.
        """

        self.loader_class.AF_disturbances_time_series(intensity = self.management_intensity).to_csv(
            os.path.join(path, "disturbance_events.csv"), index=False
        )

    def make_AF_disturbance_type(self, path):
        """
        Creates disturbance type CSV file for historic afforestation.

        Args:
            path (str): The path to the output directory.
        """
            
        self.loader_class.AF_disturbance_types().to_csv(
                os.path.join(path, "disturbance_types.csv"), index=False
            )
        
    def make_AF_transition_rules(self, path):
        """
        Creates transition rules CSV file for historic afforestation.

        Args:
            path (str): The path to the output directory.
        """
        
        transition_df=self.loader_class.AF_transition()

        # Identify columns starting with "Classifier"
        classifier_columns = [col for col in transition_df.columns if col.startswith('Classifier')]

        # Identify the index of 'DistType' to know where to insert the duplicated classifiers
        insert_index = transition_df.columns.get_loc('DistType') + 1  # +1 to insert after 'DistType'

        # Duplicate classifier columns
        duplicated_classifiers = transition_df[classifier_columns].copy()

        # Create new DataFrame with the required structure
        new_transition_df = pd.concat([
            transition_df.iloc[:, :insert_index],  # Columns before and including 'DistType'
            duplicated_classifiers,       # Duplicated classifier columns
            transition_df.iloc[:, insert_index:]   # Columns from 'DistType' onwards (excluding since it's included in the first part)
        ], axis=1)

        new_transition_df.to_csv(os.path.join(path, "transitions.csv"), index=False)

