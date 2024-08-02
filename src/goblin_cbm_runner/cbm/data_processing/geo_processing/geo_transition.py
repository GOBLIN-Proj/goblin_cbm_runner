"""
Geo Transition Module
=====================
This module provides functionalities to generate transition rules structure based on given scenario.

"""

from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
import pandas as pd
import itertools


class Transition:
    """
    Represents a transition object that generates transition rules structure based on given scenario.

    Args:
        calibration_year (int): The calibration year.
        config_path (str): The path to the configuration file.

    Attributes:
        data_manager_class (DataManager): The data manager class instance.
        baseline_forest_classifiers (dict): The baseline forest classifiers.
        scenario_forest_classifiers (dict): The scenario forest classifiers.

    Methods:
        make_transition_rules_structure: Generates the transition rules structure based on the given scenario.

    """
    def __init__(self, calibration_year, config_path):
        self.data_manager_class = GeoDataManager(calibration_year=calibration_year, config_file=config_path)
        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]

    def make_transition_rules_structure(self, scenario):
        """
        Generates a transition rules structure based on the given scenario.

        Args:
            scenario: The scenario to generate the transition rules structure for.

        Returns:
            The transition rules structure as a pandas DataFrame.
        """
        
        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
        else:
            classifiers = self.baseline_forest_classifiers

        transition_col_dict = self.data_manager_class.get_transition_cols()

        before_transition_df = pd.DataFrame(columns=transition_col_dict["before_cols"])

        after_transition_df = pd.DataFrame(columns=transition_col_dict["after_cols"])

        count = 0

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

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
                    after_transition_df.loc[count, "ResetAge"] = 1
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
                    after_transition_df.loc[count, "ResetAge"] = 1
                    after_transition_df.loc[count, "Percent"] = 100

                count += 1

        result = pd.concat([before_transition_df, after_transition_df], axis=1)

        return result
