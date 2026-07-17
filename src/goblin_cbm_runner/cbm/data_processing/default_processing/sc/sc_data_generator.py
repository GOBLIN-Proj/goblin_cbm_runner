"""
SC Data Generator
===========================
Generates scenario data for CBM simulations.

Static data (age_classes, disturbance_types, transitions, growth, classifiers)
is read directly from SC_* database tables.

Dynamic data (inventory, disturbance_events) is generated per scenario using
SCInventory and SCDisturbances classes.
"""
import os
import json
import pandas as pd

from goblin_cbm_runner.cbm.data_processing.default_processing.base import DataGenerator, save_dataframe_csv
from goblin_cbm_runner.resource_manager import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.create_json import SCCreateJSON
from goblin_cbm_runner.cbm.data_processing.default_processing.sc.sc_inventory import SCInventory
from goblin_cbm_runner.cbm.data_processing.default_processing.sc.sc_disturbances import SCDisturbances


class SCDataGenerator(DataGenerator):
    """
    Scenario data generator.

    Static data comes from SC_* database tables.
    Dynamic data (inventory, disturbance_events) is generated per scenario.

    Args:
        data_manager: SCDataManager instance
        scenario: Scenario number (0, 1, 2, ...)
    """

    def __init__(self, data_manager, scenario):
        self.data_manager = data_manager
        self.scenario = scenario
        self.loader = Loader()
        self.json_creator_class = SCCreateJSON(data_manager)
        self.inventory_class = SCInventory(data_manager)
        self.disturbances_class = SCDisturbances(data_manager, scenario)

    def generate_inventory(self, output_path: str) -> pd.DataFrame:
        """
        Generate inventory for the scenario using SCInventory.

        Loads template from SC_inventory_2100, populates areas from
        afforestation_data based on species mapping.
        """
        df = self.inventory_class.scenario_inventory(self.scenario)
        save_dataframe_csv(df, output_path, 'inventory.csv')

    def generate_classifiers(self, output_path: str) -> pd.DataFrame:
        """
        Read classifiers from SC_classifier_2100 table.
        """
        df = self.loader.SC_classifiers()
        save_dataframe_csv(df, output_path, 'classifiers.csv')

    def generate_age_classes(self, output_path: str) -> pd.DataFrame:
        """
        Read age classes from SC_age_classes_2100 table.
        """
        df = self.loader.SC_age_classes()
        save_dataframe_csv(df, output_path, 'age_classes.csv')

    def generate_disturbance_events(self, output_path: str) -> pd.DataFrame:
        """
        Generate disturbance events for the scenario.

        Uses SCDisturbances to generate DISTID4 (afforestation) and
        DISTID1/2 (harvest) events via AfforestationTracker.
        """
        # First generate inventory to get the areas
        inventory_df = self.inventory_class.scenario_inventory(self.scenario)

        # Generate disturbance events
        df = self.disturbances_class.fill_scenario_data(inventory_df)
        save_dataframe_csv(df, output_path, 'disturbance_events.csv')

    def generate_disturbance_types(self, output_path: str) -> pd.DataFrame:
        """
        Read disturbance types from SC_disturbance_types_2100 table.
        """
        df = self.loader.SC_disturbance_types()
        save_dataframe_csv(df, output_path, 'disturbance_types.csv')

    def generate_transitions(self, output_path: str) -> pd.DataFrame:
        """
        Read transitions from SC_transitions_2100 table.

        Renames from_Classifier/to_Classifier columns to standard format.
        """
        df = self.loader.SC_transitions()

        # Rename columns to standard SIT format
        for col in df.columns:
            if 'Classifier' in col:
                new_col = col.replace('from_', '').replace('to_', '')
                df.rename(columns={col: new_col}, inplace=True)

        save_dataframe_csv(df, output_path, 'transitions.csv')

    def generate_growth_curves(self, output_path: str) -> pd.DataFrame:
        """
        Read growth curves from SC_growth_2100 table.

        Filters to only include species defined in SC_classifier_2100
        to avoid libcbm validation errors.
        """
        df = self.loader.SC_growth_curves()

        # Get valid species from classifiers
        classifiers = self.loader.SC_classifiers()
        # Species classifier is classifier_id == 1
        species_classifiers = classifiers[classifiers['classifier_id'] == 1]
        # Filter out the header row (_CLASSIFIER)
        valid_species = species_classifiers[
            species_classifiers['name'] != '_CLASSIFIER'
        ]['name'].tolist()

        # Filter growth curves to only valid species
        df = df[df['Classifier1'].isin(valid_species)]

        save_dataframe_csv(df, output_path, 'growth.csv')


    def generate_config_json(self, output_path: str) -> None:
        """
        Creates a SIT configuration JSON file.

        Args:
            output_path (str): The path to the output directory.
        """
        dictionary = self.json_creator_class.populate_template()

        file = "sit_config.json"

        with open(os.path.join(output_path, file), "w") as outfile:
                json.dump(dictionary, outfile, indent=4)
