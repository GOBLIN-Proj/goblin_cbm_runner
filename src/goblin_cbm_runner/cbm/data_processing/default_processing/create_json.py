"""
Create Json Module
==================
This module is responsible for generating the configuration JSON file used by the CBM AIDB.
It provides methods to populate predefined templates with scenario-specific, or managed forest, data and mapping definitions.
"""

import copy
from goblin_cbm_runner.resource_manager import Loader
from abc import ABC, abstractmethod
from typing import Dict


class CreateJSON(ABC):
    """
    Abstract base class for creating JSON configuration files for CBM AIDB.

    This class provides the structure for generating JSON files based on different scenarios
    or managed forest data. Concrete implementations must provide methods to populate templates
    with the necessary data.
    """

    @abstractmethod
    def populate_template(self) -> Dict:
        """
        Populates the template JSON with data based on the given scenario.
        """
        pass

class AFCreateJSON(CreateJSON):
    """
    This class is responsible for creating the mapping configuration JSON for the CBM AIDB.

    Args:
        data_manager (DataManager): An instance of the DataManager class.   
    Attributes:
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (DataManager): An instance of the DataManager class.
        template (dict): The template JSON structure for the mapping configuration.
    Methods:
        populate_template: Populates the template JSON with data based on the given scenario.
    """

    def __init__(self, data_manager):
        #self.loader_class = Loader()
        self.data_manager_class = data_manager

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

    def populate_template(self):
        """
        Populates the template JSON with data based on the given scenario.

        Args:
            scenario (str): The scenario for which the mapping is being created. If None, the baseline scenario is used.

        Returns:
            dict: The populated template JSON.
        """
        template = copy.deepcopy(self.template)


        mapping = self.data_manager_class.get_cbm_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        for key in mapping["species"].keys(): 
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        for key in mapping["disturbance_types"].keys(): 
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template

class FMCreateJSON(CreateJSON):
    """
    This class is responsible for creating the mapping configuration JSON for FM baseline.

    Works with FMDataManager to create JSON configs for forest management simulation.

    Args:
        data_manager (FMDataManager): An instance of the FMDataManager class.

    Attributes:
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (FMDataManager): An instance of the FMDataManager class.
        template (dict): The template JSON structure for the mapping configuration.
        standing_vol_template (dict): The template JSON structure for the standing volume configuration.

    Methods:
        populate_template: Populates the template JSON with data based on the given scenario.
        populate_spinup_template: Populates the template JSON with data based on managed forests.
    """

    def __init__(self, data_manager):
        self.loader_class = Loader()
        self.data_manager_class = data_manager

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
                "events": {"type": "csv", "params": {"path": "historic_disturbance_events.csv"}},
                "transitions": {"type": "csv", "params": {"path": "historic_transitions.csv"}},
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

    def populate_template(self, scenario=None):
        """
        Populates the template JSON with data based on the FM config.

        For v0.6.0 FMDataManager, this uses the database-first approach:
        species and disturbance mappings come from FM_config.yaml.

        Args:
            scenario: Ignored for FM baseline (always None). Kept for interface compatibility.

        Returns:
            dict: The populated template JSON.
        """
        template = copy.deepcopy(self.template)

        # Get mapping from FMDataManager (reads from FM_config.yaml)
        mapping = self.data_manager_class.get_cbm_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        # Add species mappings
        for key in mapping["species"].keys():
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        # Add disturbance type mappings
        for key in mapping["disturbance_types"].keys():
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template

    def populate_spinup_template(self):
        """
        Populates the spinup template JSON for FM baseline.

        Uses standing volume data for spinup initialization.

        Returns:
            dict: The populated template JSON for spinup.
        """
        template = copy.deepcopy(self.standing_vol_template)

        # Get mapping from FMDataManager (reads from FM_config.yaml)
        mapping = self.data_manager_class.get_cbm_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        # Add species mappings
        for key in mapping["species"].keys():
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        # Add disturbance type mappings
        for key in mapping["disturbance_types"].keys():
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template

class SCCreateJSON(CreateJSON):
    """
    This class is responsible for creating the mapping configuration JSON for the CBM AIDB.

    Args:
        data_manager (DataManager): An instance of the DataManager class.   
    Attributes:
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (DataManager): An instance of the DataManager class.
        template (dict): The template JSON structure for the mapping configuration.
    Methods:
        populate_template: Populates the template JSON with data based on the given scenario.
    """

    def __init__(self, data_manager):
        #self.loader_class = Loader()
        self.data_manager_class = data_manager

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

    def populate_template(self):
        """
        Populates the template JSON with data based on the given scenario.

        Args:
            scenario (str): The scenario for which the mapping is being created. If None, the baseline scenario is used.

        Returns:
            dict: The populated template JSON.
        """
        template = copy.deepcopy(self.template)


        mapping = self.data_manager_class.get_cbm_mapping()

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        for key in mapping["species"].keys(): 
            try:
                template["mapping_config"]["species"]["species_mapping"].append(
                    mapping["species"][key]
                )
            except KeyError:
                continue

        for key in mapping["disturbance_types"].keys(): 
            try:
                template["mapping_config"]["disturbance_types"].append(
                    mapping["disturbance_types"][key]
                )
            except KeyError:
                continue

        return template

