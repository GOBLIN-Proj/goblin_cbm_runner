from cbm_runner.cbm_runner_data_manager import DataManager
import cbm_runner.parser as parser
import pandas as pd
import itertools
    
class Transition():
    def __init__(self, config_path):

        self.data_manager_class = DataManager(config_path)

    def make_transition_rules_structure(self):

        classifiers = self.data_manager_class.config_data["Classifiers"]

        transition_col_dict = self.data_manager_class.transition_cols

        before_transition_df = pd.DataFrame(columns=transition_col_dict["before_cols"])

        after_transition_df = pd.DataFrame(columns=transition_col_dict["after_cols"])

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

                if forest_type == "A":

                    before_transition_df.loc[count, "Classifier1"] = species
                    before_transition_df.loc[count, "Classifier2"] = "A"
                    before_transition_df.loc[count, "Classifier3"] = soil
                    before_transition_df.loc[count, "Classifier4"] = yield_class
                    before_transition_df.loc[count, "UsingID"] = False
                    before_transition_df.loc[count, "SWStart"] = 0
                    before_transition_df.loc[count, "SWEnd"] = 999
                    before_transition_df.loc[count, "HWDStart"] = 0
                    before_transition_df.loc[count, "HWEnd"] = 999
                    before_transition_df.loc[count, "DistType"] = "DISTID4"

                    after_transition_df.loc[count, "Classifier1"] = species
                    after_transition_df.loc[count, "Classifier2"] = "L"
                    after_transition_df.loc[count, "Classifier3"] = soil
                    after_transition_df.loc[count, "Classifier4"] = yield_class
                    after_transition_df.loc[count, "RegenDelay"] = 0
                    after_transition_df.loc[count, "ResetAge"] = 0
                    after_transition_df.loc[count, "Percent"] = 100

                    count += 1

        result = pd.concat([before_transition_df, after_transition_df], axis=1)

        return result