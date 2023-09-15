import pandas as pd
import math
import os
import shutil
import json
import itertools

from cbm_runner.loader import Loader
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.create_json import CreateJSON
from cbm_runner.yield_curves import YieldCurves
from cbm_runner.inventory import Inventory
from cbm_runner.disturbances import Distrubances
from cbm_runner.transition import Transition
import cbm_runner.parser as parser


from libcbm.input.sit import sit_cbm_factory


class DataFactory:
    def __init__(self, config_path, calibration_year, forest_end_year, afforestation_data, scenario_data):
        
        self.loader_class = Loader()
        self.data_manager_class = DataManager(config_path)
        self.json_creator_class = CreateJSON(config_path)
        self.inventory_class = Inventory(config_path, afforestation_data)
        self.disturbance_class = Distrubances(config_path, calibration_year, forest_end_year, afforestation_data, scenario_data)
        self.transition_class = Transition(config_path)
        self.afforestation_data = afforestation_data


    def set_input_data_dir(self, sc, path):

        sit_config_path = os.path.join(path, str(sc), "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory
    

    def set_baseline_input_data_dir(self, path):

        sit_config_path = os.path.join(path, "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        return sit, classifiers, inventory


    def make_data_dirs(self, scenarios, path):

        for sc in scenarios:
            os.mkdir(os.path.join(path, str(sc)))


    def clean_data_dir(self, path):

        for directory in os.listdir(path):
            d = os.path.join(path, directory)
            if not os.path.isfile(d):
                shutil.rmtree(d)

    def clean_baseline_data_dir(self, path):

        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) and filename != "__init__.py":
                os.remove(file_path)


    def make_config_json(self, scenario, path):

        dictionary = self.json_creator_class.populate_template(scenario)

        file = "sit_config.json"

        # Writing to outfile
        if scenario is not None:
            with open(os.path.join(path, str(scenario), file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)
        else:
            with open(os.path.join(path, file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)


    def make_classifiers(self, scenario, path):
        
        if scenario is not None:
            classifiers = self.data_manager_class.config_data["Classifiers"]["scenario_forest"]
        else:
            classifiers = self.data_manager_class.config_data["Classifiers"]["baseline_forest"]

        cols = ["classifier_id", "name", "description"]
        classifier_df = pd.DataFrame(columns=cols)

        for classifier in classifiers["classifier_id"]:

            for value, _ in enumerate(classifiers["classifier_id"][classifier]["name"]):
                name = classifiers["classifier_id"][classifier]["name"][value]
                description = classifiers["classifier_id"][classifier]["description"][
                    value
                ]

                row = pd.DataFrame([dict(zip(cols, [classifier, name, description]))])
                classifier_df = pd.concat([classifier_df, row])

        if scenario is not None:
            classifier_df.to_csv(
                os.path.join(path, str(scenario), "classifiers.csv"), index=False
            )
        else:
            classifier_df.to_csv(
                os.path.join(path, "classifiers.csv"), index=False
            )


    def make_age_classes(self, scenario, path):


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
            age_classes_df.to_csv(
                os.path.join(path, "age_classes.csv"), index=False
            )
    

    def make_yield_curves(self, scenario, path):

        yield_df = YieldCurves.yield_table_generater_method1()

        shared_classifiers = self.data_manager_class.config_data["Classifiers"]

        if scenario is not None:
            classifiers = self.data_manager_class.config_data["Classifiers"]["scenario_forest"]

        else:
            classifiers = self.data_manager_class.config_data["Classifiers"]["baseline_forest"]

        name_dict = self.data_manager_class.yield_name_dict

        max_age = shared_classifiers["age_classes"]["max_age"]
        age_interval = shared_classifiers["age_classes"]["age_interval"]

        cols = parser.get_classifier_list(classifiers)

        age_range = list(range(0, max_age + age_interval, age_interval))

        vol_cols = [f"Vol{x}" for x in range(len(age_range))]

        vol_dict = dict(zip(vol_cols, age_range))

        cols = cols + vol_cols
        growth_df = pd.DataFrame(columns=cols)

        count = 0

        for species in parser.get_inventory_species(classifiers):

            classifier_combo = [
                *[parser.get_inventory_type(classifiers, species)],
                *[parser.get_inventory_soil(classifiers, species)],
                *[parser.get_inventory_yield_class(classifiers, species)]
            ]

            combinations = itertools.product(*classifier_combo)

            for combination in combinations:
                forest_type, soil, yield_class = combination



                growth_df.loc[count, "Classifier1"] = species
                growth_df.loc[count, "Classifier2"] = forest_type
                growth_df.loc[count, "Classifier3"] = soil
                growth_df.loc[count, "Classifier4"] = yield_class
                growth_df.loc[count, "LeadSpecies"] = species

                for vol in vol_cols:
                    if vol == "Vol0":
                        growth_df.loc[count, vol] = 0

                    else:

                        if forest_type == "A":
                            growth_df.loc[count, vol] = 0

                        else:

                            if species == "CF":
                                growth_df.loc[count, vol] = yield_df.loc[
                                    name_dict[species][yield_class],
                                    vol_dict[vol],
                                ]

                            else:
                                growth_df.loc[count, vol] = yield_df.loc[
                                    name_dict[species], vol_dict[vol]
                                ]

                count += 1

        if scenario is not None:
            growth_df.to_csv(
                os.path.join(path, str(scenario), "growth.csv"), index=False
            )
        else:
            growth_df.to_csv(
                os.path.join(path, "growth.csv"), index=False
            )


    def make_inventory(self, scenario, path):


        inventory_df = self.inventory_class.make_inventory_structure(scenario, path)

        inventory_df = self.inventory_class.inventory_iterator(scenario, inventory_df)

        inventory_df = self.inventory_class.afforestation_inventory(scenario, inventory_df)


        if scenario is not None:
            inventory_df.to_csv(
                os.path.join(path, str(scenario), "inventory.csv"), index=False
            )
        else: 
            inventory_df.to_csv(
                os.path.join(path, "inventory.csv"), index=False
            )           


    def make_disturbance_events(self, scenario, path):


        disturbance_events = self.disturbance_class.fill_scenario_data(scenario)

        if scenario is not None:
            disturbance_events.to_csv(
                os.path.join(path, str(scenario), "disturbance_events.csv"), index=False
            )
        else:
            disturbance_events.to_csv(
                os.path.join(path, "disturbance_events.csv"), index=False
            )


    def make_disturbance_type(self, scenario, path):

        if scenario is not None:
            classifiers = self.data_manager_class.config_data["Classifiers"]["scenario_forest"]
        else:
            classifiers = self.data_manager_class.config_data["Classifiers"]["baseline_forest"]


        cols = ["id", "name"]
        disturbance_type_df = pd.DataFrame(columns=cols)

        disturbance_type_dict = parser.get_disturbance_type(classifiers)

        for key in disturbance_type_dict.keys():
            id = key
            description = disturbance_type_dict[key]

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

        transition_df = self.transition_class.make_transition_rules_structure(scenario)

        if scenario is not None:
            transition_df.to_csv(
                os.path.join(path, str(scenario), "transitions.csv"), index=False
            )
        else:
            transition_df.to_csv(
            os.path.join(path, "transitions.csv"), index=False
        )