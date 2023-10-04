from cbm_runner.cbm_runner_data_manager import DataManager
import cbm_runner.parser as parser
import pandas as pd
import itertools


class Transition:
    def __init__(self, calibration_year, config_path):
        self.data_manager_class = DataManager(calibration_year, config_path)
        self.baseline_forest_classifiers = self.data_manager_class.classifiers[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.classifiers[
            "Scenario"
        ]

    def make_transition_rules_structure(self, scenario):
        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
        else:
            classifiers = self.baseline_forest_classifiers

        transition_col_dict = self.data_manager_class.transition_cols

        before_transition_df = pd.DataFrame(columns=transition_col_dict["before_cols"])

        after_transition_df = pd.DataFrame(columns=transition_col_dict["after_cols"])

        count = 0

        non_forest_dict = self.data_manager_class.non_forest_dict

        species_keys = list(non_forest_dict.keys())
        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())

        for species in species_keys:
            classifier_combo = [forest_keys, soil_keys, yield_keys]

            combinations = itertools.product(*classifier_combo)

            for combination in combinations:
                forest_type, soil, yield_class = combination

                if forest_type == "A":
                    before_transition_df.loc[count, "Classifier1"] = non_forest_dict[
                        species
                    ][soil]
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

                else:
                    before_transition_df.loc[count, "Classifier1"] = species
                    before_transition_df.loc[count, "Classifier2"] = "L"
                    before_transition_df.loc[count, "Classifier3"] = soil
                    before_transition_df.loc[count, "Classifier4"] = yield_class
                    before_transition_df.loc[count, "UsingID"] = False
                    before_transition_df.loc[count, "SWStart"] = 0
                    before_transition_df.loc[count, "SWEnd"] = 999
                    before_transition_df.loc[count, "HWDStart"] = 0
                    before_transition_df.loc[count, "HWEnd"] = 999
                    before_transition_df.loc[count, "DistType"] = "DISTID1"

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
