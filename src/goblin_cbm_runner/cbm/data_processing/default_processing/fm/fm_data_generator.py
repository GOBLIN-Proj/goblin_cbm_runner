"""
FM Baseline Data Generator
===========================
Reads FM baseline data from database tables.

Database Tables Used:
- FM_inventory_2100: Forest stand inventory
- FM_transition_2100: Transition rules
- FM_disturbances_2100: Disturbance events
- FM_classifiers_2100: Classifier definitions
- FM_age_class_2100: Age class structure
- FM_disturbance_types_2100: Disturbance type definitions
- FM_growth_2100: Growth/yield curves
- FM_standing_volume_2100: Standing volume for spinup
- FM_HISTORIC_transition_2100: Historic transition rules (for spinup)
- FM_HISTORIC_disturbances_2100: Historic disturbance events (for spinup)

Key Differences from AF:
- Timeline: 2016-2070 (not 1990-2070)
- Requires spinup: YES (existing forest with standing volume)
- Database tables: FM_* (not AF_*)
- Uses separate historic disturbance/transition files for spinup configuration
"""
import os
import json
import pandas as pd
from typing import Dict

from goblin_cbm_runner.cbm.data_processing.default_processing.base import DataGenerator, save_dataframe_csv, get_classifier_columns
from goblin_cbm_runner.resource_manager import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.create_json import FMCreateJSON


class FMDataGenerator(DataGenerator):
    """
    FM Baseline data generator - reads all data from database.

    This generator is database-first: all data is pre-computed and stored
    in FM_* database tables. No config.yaml generation needed.

    Unlike AF, FM requires spinup configuration for existing forest stands.

    Args:
        data_manager: FMDataManager instance for configuration access
    """

    def __init__(self, data_manager):
        self.loader = Loader()
        self.data_manager = data_manager
        self.json_creator_class = FMCreateJSON(data_manager)

    def generate_inventory(self, output_path: str) -> pd.DataFrame:
        """
        Read inventory from FM_inventory_2100 table.

        Returns:
            DataFrame with columns: Classifier1-3, UsingID, Age, Area, Delay
        """
        df = self.loader.FM_inventory()
        save_dataframe_csv(df, output_path, 'inventory.csv')
        return df

    def generate_classifiers(self, output_path: str) -> pd.DataFrame:
        """
        Read classifiers from FM_classifiers_2100 table.

        Returns:
            DataFrame with columns: classifier_id, name, description
        """
        df = self.loader.FM_classifiers()
        save_dataframe_csv(df, output_path, 'classifiers.csv')
        return df

    def generate_age_classes(self, output_path: str) -> pd.DataFrame:
        """
        Read age classes from FM_age_class_2100 table.

        Returns:
            DataFrame with columns: id, size
        """
        df = self.loader.FM_age_class()
        save_dataframe_csv(df, output_path, 'age_classes.csv')
        return df

    def generate_disturbance_events(self, output_path: str) -> pd.DataFrame:
        """
        Read disturbance events from FM_disturbances_2100 table.

        Returns:
            DataFrame with disturbance event data
        """
        df = self.loader.FM_disturbances_time_series()
        save_dataframe_csv(df, output_path, 'disturbance_events.csv')
        return df

    def generate_disturbance_types(self, output_path: str) -> pd.DataFrame:
        """
        Read disturbance types from FM_disturbance_types_2100 table.

        Returns:
            DataFrame with columns: id, name
        """
        df = self.loader.FM_disturbance_types()
        save_dataframe_csv(df, output_path, 'disturbance_types.csv')
        return df

    def generate_transitions(self, output_path: str) -> pd.DataFrame:
        """
        Read transitions from FM_transition_2100 table and process for SIT format.

        SIT format requires classifiers before AND after transition.
        This method processes the classifier columns appropriately.

        Returns:
            DataFrame with transition rules in SIT format
        """
        df = self.loader.FM_transition()

        # Process classifier column names for SIT format
        for col in df.columns:
            if 'Classifier' in col:
                new_col = col.replace('from_', '').replace('to_', '')
                df.rename(columns={col: new_col}, inplace=True)

        save_dataframe_csv(df, output_path, 'transitions.csv')
        return df
    
    def generate_historic_transitions(self, output_path: str) -> pd.DataFrame:
        """
        Read historic transitions from FM_HISTORIC_transition_2100 table.

        Used for spinup configuration - different transition rules than
        the main simulation period.

        Returns:
            DataFrame with historic transition rules in SIT format
        """
        df = self.loader.FM_historic_transition()

        # Process classifier column names for SIT format
        for col in df.columns:
            if 'Classifier' in col:
                new_col = col.replace('from_', '').replace('to_', '')
                df.rename(columns={col: new_col}, inplace=True)

        save_dataframe_csv(df, output_path, 'historic_transitions.csv')
        return df

    def generate_historic_disturbances(self, output_path: str) -> pd.DataFrame:
        """
        Read historic disturbances from FM_HISTORIC_disturbances_2100 table.

        Used for spinup configuration - different disturbance events than
        the main simulation period.

        Returns:
            DataFrame with historic disturbance events
        """
        df = self.loader.FM_historic_disturbances()
        save_dataframe_csv(df, output_path, 'historic_disturbance_events.csv')
        return df

    def generate_growth_curves(self, output_path: str) -> pd.DataFrame:
        """
        Read growth curves from FM_growth_2100 table.

        Returns:
            DataFrame with columns: Classifier1-3, LeadSpecies, Vol0-Vol20
        """
        df = self.loader.FM_growth_curves()
        save_dataframe_csv(df, output_path, 'growth.csv')
        return df

    def generate_standing_volume(self, output_path: str) -> pd.DataFrame:
        """
        Read standing volume from FM_standing_volume_2100 table.

        This is FM-specific: used for spinup to initialize existing forest.

        Returns:
            DataFrame with standing volume data for spinup
        """
        df = self.loader.FM_standing_volume()
        save_dataframe_csv(df, output_path, 'standing_vol.csv')
        return df

    def generate_config_json(self, output_path: str) -> None:
        """
        Creates sit_config.json for FM baseline.

        Args:
            output_path (str): The path to the output directory.
        """
        dictionary = self.json_creator_class.populate_template(scenario=None)

        file = "sit_config.json"
        with open(os.path.join(output_path, file), "w") as outfile:
            json.dump(dictionary, outfile, indent=4)

    def generate_spinup_config_json(self, output_path: str) -> None:
        """
        Creates spinup_config.json for FM baseline.

        FM requires spinup using standing volume data to initialize
        existing forest carbon pools.

        Args:
            output_path (str): The path to the output directory.
        """
        dictionary = self.json_creator_class.populate_spinup_template()

        file = "spinup_config.json"
        with open(os.path.join(output_path, file), "w") as outfile:
            json.dump(dictionary, outfile, indent=4)

    def generate_all(self, output_path: str) -> None:
        """
        Generate all SIT files for FM baseline.

        Overrides base class to include FM-specific files:
        - standing_vol.csv (for spinup)
        - spinup_config.json (spinup configuration)
        - historic_transitions.csv (for spinup)
        - historic_disturbance_events.csv (for spinup)

        Args:
            output_path: Directory path to save all files
        """
        self.generate_classifiers(output_path)
        self.generate_age_classes(output_path)
        self.generate_disturbance_types(output_path)
        self.generate_inventory(output_path)
        self.generate_disturbance_events(output_path)
        self.generate_transitions(output_path)
        self.generate_growth_curves(output_path)
        self.generate_standing_volume(output_path)  # FM-specific
        self.generate_historic_transitions(output_path)  # FM-specific (spinup)
        self.generate_historic_disturbances(output_path)  # FM-specific (spinup)
        self.generate_config_json(output_path)
        self.generate_spinup_config_json(output_path)  # FM-specific
