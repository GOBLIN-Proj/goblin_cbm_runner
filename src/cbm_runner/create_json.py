import copy

from cbm_runner.loader import Loader
from cbm_runner.cbm_runner_data_manager import DataManager


class CreateJSON:
    def __init__(self, config_path):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(None, config_path, None)

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

    def populate_template(self, scenario):
        template = copy.deepcopy(self.template)

        if scenario is not None:
            config = self.data_manager_class.classifiers["Scenario"]
            disturbance = self.data_manager_class.disturbances_config["Scenario"]
        else:
            config = self.data_manager_class.classifiers["Baseline"]
            disturbance = self.data_manager_class.disturbances_config["Baseline"]

        mapping = self.data_manager_class.mapping

        template["mapping_config"]["spatial_units"]["admin_boundary"] = mapping[
            "boundary"
        ]
        template["mapping_config"]["spatial_units"]["eco_boundary"] = mapping[
            "boundary"
        ]

        for key in config[
            "Species"
        ].keys():  # mapping["species"].keys():#config["classifier_id"][1]["name"]:
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
