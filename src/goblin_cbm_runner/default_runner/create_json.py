"""
Create Json Module
==================
This module is responsible for generating the configuration JSON file used by the CBM AIDB.
It provides methods to populate predefined templates with scenario-specific, or managed forest, data and mapping definitions.
"""

import copy
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager


class CreateJSON:
    """
    This class is responsible for creating the mapping configuration JSON for the CBM AIDB.

    Args:
        config_path (str): The path to the configuration file.

    Attributes:
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (DataManager): An instance of the DataManager class.
        template (dict): The template JSON structure for the mapping configuration.
        standing_vol_template (dict): The template JSON structure for the standing volume configuration.

    Methods:
        populate_template: Populates the template JSON with data based on the given scenario.
        populate_spinup_template: Populates the template JSON with data based on managed forests.
    """

    def __init__(self, config_path):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(config_file=config_path)

        self.template = {
            "import_config": {
                "classifiers": {"type": "csv", "params": {"path": "classifiers.csv"}},
                "disturbance_types": {
                    "type": "csv",
                    "params": {"path": "disturbance_types.csv"},
                },
                "age_classes": {"type": "csv", "params": {"path": "age_classes.csv"}},
                "inventory": {"type": "csv", "params": {"path": "inventory.csv"}},
                "yield": {"type": "csv", "params": {"path": "growth.csv"}},
                "events": {"type": "csv", "params": {"path": "disturbance_events.csv"}},
                "transitions": {"type": "csv", "params": {"path": "transitions.csv"}},
            },
            "mapping_config": {
                "nonforest": None,
                "species": {
                    "species_classifier": "Species",
                    "species_mapping": [],
                },
                "spatial_units": {
                    "mapping_mode": "SingleDefaultSpatialUnit",
                    "admin_boundary": None,
                    "eco_boundary": None,
                },
                "disturbance_types": [],
            },
        }

        self.standing_vol_template = {
            "import_config": {
                "classifiers": {"type": "csv", "params": {"path": "classifiers.csv"}},
                "disturbance_types": {
                    "type": "csv",
                    "params": {"path": "disturbance_types.csv"},
                },
                "age_classes": {"type": "csv", "params": {"path": "age_classes.csv"}},
                "inventory": {"type": "csv", "params": {"path": "inventory.csv"}},
                "yield": {"type": "csv", "params": {"path": "standing_vol.csv"}},
                "events": {"type": "csv", "params": {"path": "disturbance_events.csv"}},
                "transitions": {"type": "csv", "params": {"path": "transitions.csv"}},
            },
            "mapping_config": {
                "nonforest": None,
                "species": {
                    "species_classifier": "Species",
                    "species_mapping": [],
                },
                "spatial_units": {
                    "mapping_mode": "SingleDefaultSpatialUnit",
                    "admin_boundary": None,
                    "eco_boundary": None,
                },
                "disturbance_types": [],
            },
        }

    def populate_template(self, scenario):
        """
        Populates the template JSON with data based on the given scenario.

        Args:
            scenario (str): The scenario for which the mapping is being created.

        Returns:
            dict: The populated template JSON.
        """
        template = copy.deepcopy(self.template)

        if scenario is not None:
            config = self.data_manager_class.get_classifiers()["Scenario"]
            disturbance = self.data_manager_class.get_disturbances_config()["Scenario"]
        else:
            config = self.data_manager_class.get_classifiers()["Baseline"]
            disturbance = self.data_manager_class.get_disturbances_config()["Baseline"]

        mapping = self.data_manager_class.get_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        for key in config[
            "Species"
        ].keys(): 
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        for key in disturbance:
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template
    
    def populate_spinup_template(self):
        """
        Populates the template JSON with data based on managed forests.

        Returns:
            dict: The populated template JSON.
        """
        template = copy.deepcopy(self.standing_vol_template)


        config = self.data_manager_class.get_classifiers()["Baseline"]
        disturbance = self.data_manager_class.get_disturbances_config()["Baseline"]

        mapping = self.data_manager_class.get_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        for key in config[
            "Species"
        ].keys(): 
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        for key in disturbance:
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template

