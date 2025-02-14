"""
Geo Data Manager
================

This module contains the GeoDataManager class, which manages data for the CBM Runner. 
It provides methods to access and manipulate data, including configurations, disturbance data, and scenario information.
"""
import yaml
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.cbm_pools import Pools
import pandas as pd
from goblin_cbm_runner.configuration_data import get_local_dir
import os

class GeoDataManager:
    """
    Manages data for CBM Runner.

    Provides methods to access and manipulate data, including configurations, disturbance data, and scenario information.

    Attributes:
        config_data (dict): Configuration data from a YAML file.
        forest_baseline_year (int): The baseline (calibration) year for forest data.
        cbm_default_config (dict): The default CBM configuration.
        non_forest_dict (dict): Non-forest dictionary for afforestation types.
        non_forest_soils (dict): Non-forest soils types.
        forest_type_keys (dict): Forest type keys from CBM default configuration.
        soils_dict (dict): Soils dictionary from CBM default configuration.
        classifiers (dict): Classifiers from CBM default configuration.
        disturbances_config (dict): Disturbances configuration from CBM default configuration.
        yield_name_dict (dict): Species yield name dictionary from CBM default configuration.
        species_name_dict (dict): Species name dictionary from CBM default configuration.
        afforestation_yield_name_dict (dict): Afforestation yield name dictionary from CBM default configuration.
        yield_baseline_dict (dict): Yield baseline dictionary from CBM default configuration.
        disturbance_cols (dict): Disturbance columns from CBM default configuration.
        static_disturbance_cols (dict): Static disturbance columns from CBM default configuration.
        transition_cols (dict): Transition columns from CBM default configuration.
        mapping (dict): AIDB mapping from CBM default configuration.
        scenario_data (pd.DataFrame): Scenario data.
        scenario_disturbance_dict (dict): Scenario disturbance dictionary.

    Parameters:
        calibration_year (int, optional): The year used for calibration. Defaults to None.
        config_file_path (str, optional): Path to the configuration file. Defaults to None.
        scenario_data (pd.DataFrame, optional): Dataframe containing scenario data. Defaults to None.
        afforest_data (pd.DataFrame, optional): Dataframe containing afforestation data. Defaults to None.
        sit_path (str, optional): Path to the SIT file. Defaults to None.
    """

    def __init__(self, calibration_year, 
                 config_file_path, 
                 scenario_data, 
                 afforest_data, 
                 sit_path = None):

        self.sit_path = sit_path
        self.CBMpools = Pools()
        self.config_file_path = config_file_path
        self.config_data = self.get_config_data(self.config_file_path) if self.config_file_path else None

        self.forest_baseline_year = (
            (int(calibration_year)) if calibration_year is not None else None
        )

        self.forest_end_year = 2100

        self.cbm_default_config = self.get_config_data(os.path.join(get_local_dir(), "geo_config.yaml"))
    
        self.non_forest_dict = self.cbm_default_config.get("non_forest_dict", {})
        self.non_forest_soils = self.cbm_default_config.get("non_forest_soils", {})
        self.forest_type_keys = self.cbm_default_config.get("forest_type_keys", {})
        self.soils_dict = self.cbm_default_config.get("soils_dict", {})
        self.classifiers = self.cbm_default_config.get("classifiers", {})
        self.disturbances_config = self.cbm_default_config.get("disturbances", {})
        self.yield_name_dict = self.cbm_default_config.get("yield_name_dict", {})
        self.species_name_dict = self.cbm_default_config.get("species_name_dict", {})
        self.afforestation_yield_name_dict = self.cbm_default_config.get("afforestation_yield_name_dict", {})
        self.yield_baseline_dict = self.cbm_default_config.get("yield_baseline_dict", {})
        self.disturbance_cols = self.cbm_default_config.get("disturbance_cols", {})
        self.static_disturbance_cols = self.cbm_default_config.get("static_disturbance_cols", {})
        self.transition_cols = self.cbm_default_config.get("transition_cols", {})
        self.mapping = self.cbm_default_config.get("mapping", {})
        self.transition_dicts = self.cbm_default_config.get("transition_dicts", {})
        self.sort_dict = self.cbm_default_config.get("SortType", {})

        self.afforestation_data = afforest_data

        self.scenario_data = (
            scenario_data if scenario_data is not None else pd.DataFrame()
        )

        self.scenario_disturbance_dict = (
            self.gen_scenario_disturbance_dict(scenario_data)
            if not self.scenario_data.empty
            else None
        )


    def get_config_file_path(self):
        """
        Get the path to the configuration file.

        Returns:
            str: The path to the configuration file.
        """
        return self.config_file_path

    def get_sit_path(self):
        """
        Get the path to the SIT file.

        Returns:
            str: The path to the SIT file.
        """
        return self.sit_path
    

    def get_config_data(self, config_file):
        """
        Load and return the configuration data from the specified file.

        Args:
            config_file (str): The path to the configuration file.

        Returns:
            dict: The configuration data loaded from the file.
        """
        if config_file:
            with open(config_file, "r") as file:
                config_data = yaml.safe_load(file)
            return config_data
    

    def get_non_forest_dict(self):
        """
        Get the non-forest dictionary.

        Returns:
            dict: The non-forest dictionary.
        """
        return self.non_forest_dict
    

    def get_non_forest_soils(self):
        """
        Get the non-forest soils dictionary.

        Returns:
            dict: The non-forest soils dictionary.
        """
        return self.non_forest_soils
    
    def get_forest_type_keys(self):
        """
        Get the forest type keys.

        Returns:
            dict: The forest type keys.
        """
        return self.forest_type_keys
    
    def get_soils_dict(self):
        """
        Get the soils dictionary.

        Returns:
            dict: The soils dictionary.
        """
        return self.soils_dict
    
    def get_classifiers(self):
        """
        Get the classifiers dictionary.

        Returns:
            dict: The classifiers dictionary.
        """
        return self.classifiers
    
    def get_disturbances_config(self):
        """
        Get the disturbances configuration.

        Returns:
            dict: The disturbances configuration.
        """
        return self.disturbances_config
    
    def get_yield_name_dict(self):
        """
        Get the species yield name dictionary.

        Returns:
            dict: The species yield name dictionary.
        """  
        return self.yield_name_dict
    
    def get_species_name_dict(self):
        """
        Get the species name dictionary.
        
        Returns:
            dict: The species name dictionary.
        """
        return self.species_name_dict
    
    def get_afforestation_yield_name_dict(self):
        """
        Get the afforestation yield name dictionary.
        
        Returns:
            dict: The afforestation yield name dictionary.
        """
        return self.afforestation_yield_name_dict
    
    def get_yield_baseline_dict(self):
        """
        Get the yield baseline dictionary.

        Returns:
            dict: The yield baseline dictionary.
        """
        return self.yield_baseline_dict
    
    def get_disturbance_cols(self):
        """
        Get the disturbance columns.

        Returns:
            list: A list of disturbance columns.
        """
        return self.disturbance_cols
    
    def get_static_disturbance_cols(self):
        """
        Get the static disturbance columns.

        Returns:
            list: A list of static disturbance columns.
        """
        return self.static_disturbance_cols
    
    def get_transition_cols(self):
        """
        Get the transition columns.

        Returns:
            list: A list of transition columns.
        """
        return self.transition_cols
    
    def get_mapping(self):
        """
        Get the AIDB mapping.

        Returns:
            dict: The AIDB mapping.
        """
        return self.mapping

    
    def get_scenario_data(self):
        """
        Get the scenario data.
        
        Returns:
            pd.DataFrame: The scenario data.
        """
        return self.scenario_data

    def get_scenario_disturbance_dict(self):
        """
        Get the scenario disturbance dictionary.

        Returns:
            dict: The scenario disturbance dictionary.
        """
        return self.scenario_disturbance_dict


    def gen_scenario_disturbance_dict(self, scenario_data):
        """
        Generate a dictionary of disturbance data for each scenario.

        Args:
            scenario_data (pd.DataFrame): The input scenario data.

        Returns:
            dict: A dictionary containing disturbance data for each scenario.
        """
        grouped_data = scenario_data.drop_duplicates(
            subset=["Scenarios", "Conifer harvest", "Conifer thinned"]
        ).reset_index(drop=True)

        clearfell_broadleaf = parser.get_runner_clearfell_scenario(self.config_data, "broadleaf")
        broadleaf_thinning = parser.get_runner_thinning_scenario(self.config_data, "broadleaf")

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
            scenario_disturbance_dict[scenario]["SGB"]["DISTID1"] = clearfell_broadleaf

            scenario_disturbance_dict[scenario]["Sitka"]["DISTID2"] = grouped_data.loc[
                mask, "Conifer thinned"
            ].item()
            scenario_disturbance_dict[scenario]["SGB"]["DISTID2"] = broadleaf_thinning

        scenario_disturbance_dict = self.get_baseline_disturbance_dict(
            scenario_disturbance_dict
        )

        return scenario_disturbance_dict
    

    def get_baseline_disturbance_dict(self, scenario_dist):
        """
        Get the baseline disturbance dictionary and add it to the scenario disturbance dictionary.

        Args:
            scenario_dist (dict): The scenario disturbance dictionary.

        Returns:
            dict: The updated scenario disturbance dictionary with baseline disturbances.
        """
        clearfell_conifer = parser.get_runner_clearfell_baseline(self.config_data, "conifer")
        clearfell_broadleaf = parser.get_runner_clearfell_baseline(self.config_data, "broadleaf")
        conifer_thinning = parser.get_runner_thinning_baseline(self.config_data, "conifer")
        broadleaf_thinning = parser.get_runner_thinning_baseline(self.config_data, "broadleaf")

        scenario_dist[-1] = {}
        scenario_dist[-1]["Sitka"] = {}
        scenario_dist[-1]["SGB"] = {}
        scenario_dist[-1]["CBmix"] = {}
        scenario_dist[-1]["Sitka"]["DISTID1"] = clearfell_conifer
        scenario_dist[-1]["CBmix"]["DISTID1"] = clearfell_conifer
        scenario_dist[-1]["SGB"]["DISTID1"] = clearfell_broadleaf
        scenario_dist[-1]["Sitka"]["DISTID2"] = conifer_thinning
        scenario_dist[-1]["CBmix"]["DISTID2"] = conifer_thinning
        scenario_dist[-1]["SGB"]["DISTID2"] = broadleaf_thinning

        return scenario_dist

    
    def get_baseline_years(self, forestry_end_year):
        """
        Get the number of baseline years.

        Args:
            forestry_end_year (int): The end year for forestry.

        Returns:
            int: The number of years in the baseline.
        """
        forest_baseline_year = self.get_calibration_year()
        years = forestry_end_year - forest_baseline_year
        return years
    
    def get_baseline_years_range(self, forestry_end_year):
        """
        Get the range of baseline years.

        Args:
            forestry_end_year (int): The end year for forestry.

        Returns:
            list: The range of years in the baseline.
        """
        forest_baseline_year = self.get_calibration_year()
        years_range = list(range(forest_baseline_year, forestry_end_year + 1))
        return years_range
    
    def get_forest_end_year(self):
        """
        Get the forest end year.

        Returns:
            int: The forest end year.
        """
        return self.forest_end_year
    
    def get_transition_dict_species(self):
        """
        Get the transition dictionaries for species.

        Returns:
            dict: The transition dictionaries for species.
        """
        return self.transition_dicts.get("Transition_Species", {})
    

    def get_transition_dict_species_to_yield(self):
        """
        Get the transition dictionaries for species to yield.

        Returns:
            dict: The transition dictionaries for species to yield.
        """
        return self.transition_dicts.get("Afforest_Species_to_Yield", {})
    

    def get_afforestation_data(self):
        """
        Get the afforestation data.

        Returns:
            pd.DataFrame: The afforestation data.
        """
        return self.afforestation_data
    
    def get_calibration_year(self):
        """
        Get the calibration year.

        NOTE: Replaces get_forest_baseline_year().

        Returns:
            int: The calibration year.
        """
        return self.forest_baseline_year

    def get_sort_dict(self):
        """
        Get the sort dictionary.

        Returns:
            dict: The sort dictionary.
        """
        return self.sort_dict