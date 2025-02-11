"""
CBM Runner Data Manager
=======================
This module contains the DataManager class, which manages data for the CBM Runner.
"""
import yaml
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.cbm_pools import Pools
import pandas as pd
from goblin_cbm_runner.configuration_data import get_local_dir
import os

class DataManager:
    """
    Manages data for CBM Runner.

    Attributes:
        config_data (dict): Configuration data from a YAML file.
        forest_baseline_year (int): Baseline year for forest data.
        afforestation_baseline (int): Baseline year for afforestation.
        cbm_default_config (dict): Default CBM configuration.
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
        scenario_data (DataFrame): Scenario data.
        scenario_disturbance_dict (dict): Scenario disturbance dictionary.
        transition_dicts (dict): Transition dictionaries from CBM default configuration.
        sort_dict (dict): Sort type dictionary from CBM default configuration.

    Parameters:
        calibration_year (int): Year used for calibration.
        config_file_path (str): Path to the configuration file.
        scenario_data (DataFrame): Dataframe containing scenario data.
        afforest_data (DataFrame): Dataframe containing afforestation data.
        sit_path (str, optional): Path to the SIT file. Defaults to None.
    """

    def __init__(self, 
                 calibration_year, 
                 config_file_path, 
                 scenario_data, 
                 afforest_data, 
                 sit_path = None
):
        
        self.sit_path = sit_path
        self.CBMpools = Pools()
        self.config_file_path = config_file_path
        self.config_data = self.get_config_data(self.config_file_path) if self.config_file_path else None

        self.forest_baseline_year = 2016 

        self.calibration_year = calibration_year

        self.afforestation_baseline = 1990

        self.forest_end_year = 2100

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
        self.yield_baseline_dict = self.cbm_default_config.get("yield_baseline_dict", {})
        self.disturbance_cols = self.cbm_default_config.get("disturbance_cols", {})
        self.static_disturbance_cols = self.cbm_default_config.get("static_disturbance_cols", {})
        self.transition_cols = self.cbm_default_config.get("transition_cols", {})
        self.mapping = self.cbm_default_config.get("mapping", {})
        self.transition_dicts = self.cbm_default_config.get("transition_dicts", {})
        self.sort_dict = self.cbm_default_config.get("SortType", {})
    

        self.scenario_data = (
            scenario_data if scenario_data is not None else pd.DataFrame()
        )

        self.scenario_disturbance_dict = (
            self.gen_scenario_disturbance_dict(scenario_data)
            if not self.scenario_data.empty
            else None
        )

        self.afforest_data = afforest_data

    def get_config_file_path(self):
        """
        Get the path to the configuration file.

        Returns:
            str: Path to the configuration file.
        """
        return self.config_file_path

    def get_sit_path(self):
        """
        Get the path to the SIT file.

        Returns:
            str: Path to the SIT file.
        """
        return self.sit_path
    
    
    def get_forest_management_intensity(self):
        """
        Get the forest management intensity.

        Returns:
            dict: Forest management intensity.
        """
        return parser.get_forest_management_intensity(self.config_data)
    

    def get_afforest_data(self):
        """
        Get the afforestation data.

        Returns:
            DataFrame: Afforestation data.
        """
        return self.afforest_data
    
    
    def get_config_data(self, config_file):
        """
        Load and return the configuration data from the specified file.

        Args:
            config_file (str): Path to the configuration file.

        Returns:
            dict: Configuration data loaded from the file.
        """
        if config_file:
            with open(config_file, "r") as file:
                config_data = yaml.safe_load(file)
            return config_data
    

    def get_non_forest_dict(self):
        """
        Retrieve the non-forest dictionary.

        Returns:
            dict: Non-forest dictionary.
        """
        return self.non_forest_dict
    

    def get_non_forest_soils(self):
        """
        Retrieve the non-forest soils dictionary.

        Returns:
            dict: Non-forest soils dictionary.
        """
        return self.non_forest_soils
    
    def get_forest_type_keys(self):
        """
        Retrieve the forest type dictionary.

        Returns:
            dict: Forest type dictionary.
        """
        return self.forest_type_keys
    
    def get_soils_dict(self):
        """
        Retrieve the soils dictionary.

        Returns:
            dict: Soils dictionary.
        """
        return self.soils_dict
    
    def get_classifiers(self):
        """
        Retrieve the classifiers dictionary.

        Returns:
            dict: Classifiers dictionary.
        """
        return self.classifiers
    
    def get_disturbances_config(self):
        """
        Retrieve the disturbance ID dictionary for scenarios and baseline.

        Returns:
            dict: Disturbance ID dictionary.
        """
        return self.disturbances_config
    
    def get_yield_name_dict(self):
        """
        Retrieve the yield name dictionary.

        Returns:
            dict: Yield name dictionary.
        """  
        return self.yield_name_dict
    
    def get_species_name_dict(self):
        """
        Get the dictionary mapping species IDs to their names.
        
        Returns:
            dict: Dictionary where keys are species growth curve IDs and values are species names.
        """
        return self.species_name_dict
    
    def get_afforestation_yield_name_dict(self):
        """
        Return the dictionary containing the names of afforestation yield classes.
        
        Returns:
            dict: Dictionary containing the names of afforestation yield classes.
        """
        return self.afforestation_yield_name_dict
    
    def get_yield_baseline_dict(self):
        """
        Return the yield baseline dictionary.

        Returns:
            dict: Yield baseline dictionary where keys are yield classes and values are the proportions of that yield class nationally.
        """
        return self.yield_baseline_dict
    
    def get_disturbance_cols(self):
        """
        Return the disturbance columns used in the disturbance dataframe generator.

        Returns:
            list: List of disturbance columns.
        """
        return self.disturbance_cols
    
    def get_static_disturbance_cols(self):
        """
        Return the static disturbance columns used in the disturbance dataframe generator.

        Returns:
            list: List of static disturbance columns.
        """
        return self.static_disturbance_cols
    
    def get_transition_cols(self):
        """
        Return the transition columns used in the transition dataframe generator.

        Returns:
            list: List of transition columns.
        """
        return self.transition_cols
    
    def get_transition_dict_species(self):
        """
        Return the transition dictionaries used in the transition dataframe generator.

        Returns:
            dict: Dictionary of transition dictionaries.
        """
        return self.transition_dicts.get("Transition_Species", {})
    

    def get_transition_dict_species_to_yield(self):
        """
        Get the transition dictionaries.

        Returns:
            dict: The transition dictionaries.
        """
        return self.transition_dicts.get("Afforest_Species_to_Yield", {})
    

    def get_mapping(self):
        """
        Return the mapping used by the data manager to map parameters to the CBM AIDB.

        Returns:
            dict: Mapping used by the data manager.
        """
        return self.mapping
    
    def get_calibration_year(self):
        """
        Get the calibration year.

        Returns:
            int: Calibration year.
        """
        return self.calibration_year
    
    def get_forest_baseline_year(self):
        """
        Get the forest baseline year, which is equal to the calibration year.

        Returns:
            int: Forest baseline year.
        """
        return self.forest_baseline_year
    
    def get_afforestation_baseline(self):
        """
        Return the afforestation baseline, default is 1990.

        Returns:
            int: Afforestation baseline (1990).
        """
        return self.afforestation_baseline
    
    def get_forest_end_year(self):
        """
        Get the forest end year.

        Returns:
            int: Forest end year.
        """
        return self.forest_end_year
    
    def get_scenario_data(self):
        """
        Return the goblin scenario data, used to retrieve the harvest and thinning proportions for scenarios.
        
        Returns:
            DataFrame: Scenario data.
        """
        return self.scenario_data

    def get_scenario_disturbance_dict(self):
        """
        Return the scenario and baseline disturbance ID dictionary.

        Returns:
            dict: Scenario and baseline disturbance ID dictionary.
        """
        return self.scenario_disturbance_dict


    def gen_scenario_disturbance_dict(self, scenario_data):
        """
        Generate a dictionary of disturbance data for each scenario.

        Args:
            scenario_data (DataFrame): Input scenario data.

        Returns:
            dict: Dictionary containing disturbance data for each scenario.
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
        Get the baseline disturbance dictionary. This is added to the scenario disturbance dictionary.

        Args:
            scenario_dist (dict): Scenario disturbance dictionary.

        Returns:
            dict: Updated scenario disturbance dictionary with baseline disturbances.
        """
        clearfell_conifer = parser.get_runner_clearfell_baseline(self.config_data, "conifer")
        clearfell_broadleaf = parser.get_runner_clearfell_baseline(self.config_data, "broadleaf")
        conifer_thinning = parser.get_runner_thinning_baseline(self.config_data, "conifer")
        broadleaf_thinning = parser.get_runner_thinning_baseline(self.config_data, "broadleaf")

        scenario_dist[-1] = {}
        scenario_dist[-1]["Sitka"] = {}
        scenario_dist[-1]["SGB"] = {}
        scenario_dist[-1]["Sitka"]["DISTID1"] = clearfell_conifer
        scenario_dist[-1]["SGB"]["DISTID1"] = clearfell_broadleaf
        scenario_dist[-1]["Sitka"]["DISTID2"] = conifer_thinning
        scenario_dist[-1]["SGB"]["DISTID2"] = broadleaf_thinning

        return scenario_dist

    
    def get_full_scenario_years(self, forestry_end_year):
        """
        Get total number of scenario years from 1990.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            int: Number of years in the scenario.
        """
        forest_baseline_year = self.get_afforestation_baseline()

        years = forestry_end_year - forest_baseline_year

        return years
    
    def calculate_scenario_years(self,forestry_end_year):
        """
        Calculate the number of years in the scenario from the calibration year.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            int: Number of years in the scenario.
        """

        years = forestry_end_year - self.calibration_year

        return years
    
    def calculate_scenario_years_range(self, forestry_end_year):
        """
        Calculate the range of years in the scenario from the calibration year.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            list: Range of years in the scenario.
        """
        years_range = list(range(self.calibration_year, forestry_end_year + 1))

        return years_range


    def get_full_scenario_years_range(self, forestry_end_year):
        """
        Get the scenario years range, including afforestation from 1990.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            list: Range of years in the scenario.
        """
        forest_baseline_year = self.get_afforestation_baseline()

        years_range = list(range(forest_baseline_year, forestry_end_year + 1))

        return years_range
    
    
    def get_baseline_years(self, forestry_end_year):
        """
        Get the baseline years.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            int: Number of years in the baseline.
        """
        forest_baseline_year = self.get_forest_baseline_year()

        years = forestry_end_year - forest_baseline_year

        return years
    
    
    def get_baseline_years_range(self, forestry_end_year):
        """
        Get the baseline years range.

        Args:
            forestry_end_year (int): Year at the end of the scenario.

        Returns:
            list: Range of years in the baseline.
        """
        forest_baseline_year = self.get_forest_baseline_year()

        years_range = list(range(forest_baseline_year, forestry_end_year + 1))

        return years_range


    def get_afforest_delay(self):
        """
        Get the afforestation delay.

        Returns:
            int: Afforestation delay.
        """
        afforest_delay = parser.get_afforest_delay(self.config_data)

        return afforest_delay
    

    def get_annual_afforestation_rate(self):
        """
        Get the annual afforestation rate for delay years.

        Returns:
            float: Annual afforestation rate.
        """
        annual_afforestation_rate = parser.get_annual_afforestation_rate(self.config_data)

        return annual_afforestation_rate
    

    def get_afforestation_species_distribution(self, species):
        """
        Get the afforestation rate species distribution.

        Args:
            species (str): Species name.

        Returns:
            float: Afforestation rate species distribution.
        """
        species_distribution = parser.get_afforestation_species_distribution(self.config_data, species)

        return species_distribution
    
    def get_sort_dict(self):
        """
        Get the sort dictionary.

        Returns:
            dict: Sort dictionary.
        """
        return self.sort_dict