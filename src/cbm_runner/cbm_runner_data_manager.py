import yaml
import cbm_runner.parser as parser
import pandas as pd
from cbm_runner.config_data import get_local_dir
import os

class DataManager:
    def __init__(self, calibration_year=None, config_file=None, scenario_data=None):
        self.config_data = self.get_config_data(config_file) if config_file else None

        self.forest_baseline_year = (
            (int(calibration_year) - 1) if calibration_year is not None else None
        )

        self.afforestation_baseline = 1990

        self.cbm_default_config = self.get_config_data(os.path.join(get_local_dir(), "config.yaml"))
    
        self.non_forest_dict = self.cbm_default_config.get("non_forest_dict", {})
        self.non_forest_soils = self.cbm_default_config.get("non_forest_soils", {})
        self.forest_type_keys = self.cbm_default_config.get("forest_type_keys", {})
        self.soils_dict = self.cbm_default_config.get("soils_dict", {})
        self.classifiers = self.cbm_default_config.get("classifiers", {})
        self.disturbances_config = self.cbm_default_config.get("disturbances", {})
        self.yield_name_dict = self.cbm_default_config.get("yield_name_dict", {})
        self.species_name_dict = self.cbm_default_config.get("species_name_dict", {})
        self.afforestation_yield_name_dict = self.cbm_default_config.get("afforestation_yield_name_dict", {})
        self.yield_basline_dict = self.cbm_default_config.get("yield_basline_dict", {})
        self.disturbance_cols = self.cbm_default_config.get("disturbance_cols", {})
        self.static_disturbance_cols = self.cbm_default_config.get("static_disturbance_cols", {})
        self.transition_cols = self.cbm_default_config.get("transition_cols", {})
        self.mapping = self.cbm_default_config.get("mapping", {})



        self.scenario_data = (
            scenario_data if scenario_data is not None else pd.DataFrame()
        )

        self.scenario_disturbance_dict = (
            self.gen_scenario_disturbance_dict(scenario_data)
            if not self.scenario_data.empty
            else None
        )

    def get_non_forest_dict(self):
        return self.non_forest_dict
    
    def get_non_forest_soils(self):
        return self.non_forest_soils
    
    def get_forest_type_keys(self):
        return self.forest_type_keys
    
    def get_soils_dict(self):
        return self.soils_dict
    
    def get_classifiers(self):
        return self.classifiers
    
    def get_disturbances_config(self):
        return self.disturbances_config
    
    def get_yield_name_dict(self):  
        return self.yield_name_dict
    
    def get_species_name_dict(self):
        return self.species_name_dict
    
    def get_afforestation_yield_name_dict(self):
        return self.afforestation_yield_name_dict
    
    def get_yield_basline_dict(self):    
        return self.yield_basline_dict
    
    def get_disturbance_cols(self):
        return self.disturbance_cols
    
    def get_static_disturbance_cols(self):
        return self.static_disturbance_cols
    
    def get_transition_cols(self):
        return self.transition_cols
    
    def get_mapping(self):
        return self.mapping
    
    def get_forest_baseline_year(self):
        return self.forest_baseline_year
    
    def get_afforestation_baseline(self):
        return self.afforestation_baseline
    
    def get_scenario_data(self):
        return self.scenario_data   
    
    def get_scenario_disturbance_dict(self):
        return self.scenario_disturbance_dict   


    def get_config_data(self, config_file):
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)

        return config_data


    def gen_scenario_disturbance_dict(self, scenario_data):
        grouped_data = scenario_data.drop_duplicates(
            subset=["Scenarios", "Conifer harvest", "Conifer thinned"]
        ).reset_index(drop=True)

        scenario_disturbance_dict = {}

        for sc in grouped_data.Scenarios:
            scenario = sc
            mask = grouped_data.Scenarios == sc

            scenario_disturbance_dict[scenario] = {}
            scenario_disturbance_dict[scenario]["Sitka"] = {}
            scenario_disturbance_dict[scenario]["SGB"] = {}

            scenario_disturbance_dict[scenario]["Sitka"]["DISTID1"] = grouped_data.loc[
                mask, "Conifer harvest"
            ].item()
            scenario_disturbance_dict[scenario]["SGB"]["DISTID1"] = 0

            scenario_disturbance_dict[scenario]["Sitka"]["DISTID2"] = grouped_data.loc[
                mask, "Conifer thinned"
            ].item()
            scenario_disturbance_dict[scenario]["SGB"]["DISTID2"] = 0

        scenario_disturbance_dict = self.get_baseline_disturbance_dict(
            scenario_disturbance_dict
        )
        return scenario_disturbance_dict
    

    def get_baseline_disturbance_dict(self, scenario_dist):
        
        clearfell = parser.get_clearfell_baseline(self.config_data)
        thinning = parser.get_thinning_baseline(self.config_data)

        scenario_dist[-1] = {}
        scenario_dist[-1]["Sitka"] = {}
        scenario_dist[-1]["SGB"] = {}
        scenario_dist[-1]["Sitka"]["DISTID1"] = clearfell
        scenario_dist[-1]["SGB"]["DISTID1"] = 0
        scenario_dist[-1]["Sitka"]["DISTID2"] = thinning

        return scenario_dist
    
    def get_legacy_disturbance_dict(self):
        clearfell = parser.get_clearfell_baseline(self.config_data)
        thinning = parser.get_thinning_baseline(self.config_data)

        legacy_dist = {}
        legacy_dist["DISTID1"] = clearfell
        legacy_dist["DISTID2"] = thinning

        return legacy_dist 


