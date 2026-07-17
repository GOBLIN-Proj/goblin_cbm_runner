"""
AF Baseline Data Generator
===========================
Reads AF baseline data from database tables.

Database Tables Used:
- AF_inventory_2100: Forest stand inventory
- AF_transitions_2100: Transition rules
- AF_disturbance_2100: Disturbance events
- AF_classifier_2100: Classifier definitions
- AF_age_classes_2100: Age class structure
- AF_disturbance_types_2100: Disturbance type definitions
- AF_growth_2100: Growth/yield curves
"""
import os
import json
import pandas as pd
from typing import Dict

from goblin_cbm_runner.cbm.data_processing.default_processing.base import DataGenerator, save_dataframe_csv, get_classifier_columns
from goblin_cbm_runner.resource_manager import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.create_json import AFCreateJSON


class AFDataGenerator(DataGenerator):
    """
    AF Baseline data generator - reads all data from database.

    This generator is database-first: all data is pre-computed and stored
    in AF_* database tables. No config.yaml generation needed.

    Args:
        loader: Loader instance for database access
    """

    def __init__(self, data_manager):
        self.loader = Loader()
        self.json_creator_class = AFCreateJSON(data_manager)

    def generate_inventory(self, output_path: str) -> pd.DataFrame:
        """
        Read inventory from AF_inventory_2100 table.

        Returns:
            DataFrame with columns: Classifier1-4, UsingID, Age, Area, Delay
        """
        df = self.loader.AF_inventory()
        save_dataframe_csv(df, output_path, 'inventory.csv')


    def generate_classifiers(self, output_path: str) -> pd.DataFrame:
        """
        Read classifiers from AF_classifier_2100 table.

        Returns:
            DataFrame with columns: classifier_id, name, description
        """
        df = self.loader.AF_classifiers()
        save_dataframe_csv(df, output_path, 'classifiers.csv')


    def generate_age_classes(self, output_path: str) -> pd.DataFrame:
        """
        Read age classes from AF_age_classes_2100 table.

        Returns:
            DataFrame with columns: id, size
        """
        df = self.loader.AF_age_class()
        save_dataframe_csv(df, output_path, 'age_classes.csv')


    def generate_disturbance_events(self, output_path: str) -> pd.DataFrame:
        """
        Read disturbance events from AF_disturbance_2100 table.

        Returns:
            DataFrame with disturbance event data (36 columns)
        """
        df = self.loader.AF_disturbances_time_series()
        save_dataframe_csv(df, output_path, 'disturbance_events.csv')


    def generate_disturbance_types(self, output_path: str) -> pd.DataFrame:
        """
        Read disturbance types from AF_disturbance_types_2100 table.

        Returns:
            DataFrame with columns: id, name
        """
        df = self.loader.AF_disturbance_types()
        save_dataframe_csv(df, output_path, 'disturbance_types.csv')


    def generate_transitions(self, output_path: str) -> pd.DataFrame:
        """
        Read transitions from AF_transitions_2100 table and process for SIT format.

        SIT format requires classifiers before AND after transition.
        This method duplicates the classifier columns.

        Returns:
            DataFrame with transition rules in SIT format
        """
        df = self.loader.AF_transition()

        for col in df.columns:
            if 'Classifier' in col:
                new_col = col.replace('from_', '').replace('to_', '')
                df.rename(columns={col: new_col}, inplace=True)

        save_dataframe_csv(df, output_path, 'transitions.csv')


    def generate_growth_curves(self, output_path: str) -> pd.DataFrame:
        """
        Read growth curves from AF_growth_2100 table.

        Returns:
            DataFrame with columns: Classifier1-4, LeadSpecies, Vol0-Vol20
        """
        df = self.loader.AF_growth_curves()
        save_dataframe_csv(df, output_path, 'growth.csv')


    def generate_config_json(self, output_path: str) -> None:
        """
        Creates a configuration JSON file.

        Args:
            scenario (int): The scenario number.
            path (str): The path to the output directory.
        """
        # Route AF baseline (scenario=-1) to AF generator

        dictionary = self.json_creator_class.populate_template()

        file = "sit_config.json"

        with open(os.path.join(output_path, file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)
