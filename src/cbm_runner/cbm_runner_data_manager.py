import yaml
import cbm_runner.parser as parser
import pandas as pd
from cbm_runner.config_data import get_local_dir
import os

class DataManager:
    """
    Manages data for CBM Runner.

    This class provides methods to access and manipulate data relevant to the CBM Runner, 
    including configurations, disturbance data, and scenario information.

    Attributes:
        config_data (dict): Configuration data from a YAML file.
        forest_baseline_year (int): The baseline (calibration) year for forest data.
        afforestation_baseline (int): The baseline year for afforestation.
        cbm_default_config (dict): The default CBM configuration.
        non_forest_dict (dict): Non-forest dictionary for afforestation types.
        non_forest_soils (dict): Non-forest soils types, split between mineral and peat.
        forest_type_keys (dict): Forest type keys from CBM default configuration (Legacy and Afforestation classifiers).
        soils_dict (dict): Soils dictionary from CBM default configuration, afforestation pre types (for initial SOC).
        classifiers (dict): Classifiers from CBM default configuration.
        disturbances_config (dict): Disturbances configuration for scenario and baseline from CBM default configuration.
        yield_name_dict (dict): Species yield name dictionary relating species to growth curves from CBM default configuration.
        species_name_dict (dict): Species name dictionary from CBM default configuration.
        afforestation_yield_name_dict (dict): Afforestation yield name dictionary from CBM default configuration.
        yield_baseline_dict (dict): Yield baseline dictionary relating the proprotional split, nationally, of yields by species from CBM default configuration.
        disturbance_cols (dict): Disturbance columns from CBM default configuration.
        static_disturbance_cols (dict): Static disturbance columns from CBM default configuration.
        transition_cols (dict): Transition columns from CBM default configuration.
        mapping (dict): AIDB mapping from CBM default configuration.
        scenario_data (DataFrame): Scenario data.
        scenario_disturbance_dict (dict): Scenario disturbance dictionary.

    Parameters:
        calibration_year (int, optional): The year used for calibration. Defaults to None.
        config_file (str, optional): Path to the configuration file. Defaults to None.
        scenario_data (DataFrame, optional): Dataframe containing scenario data. Defaults to None.
    """

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
        self.yield_baseline_dict = self.cbm_default_config.get("yield_baseline_dict", {})
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
        """
        Retrieves the non-forest dictionary.

        Returns:
            dict: The non-forest dictionary.
        """
        return self.non_forest_dict
    

    def get_non_forest_soils(self):
        """
        Retrieves the non-forest soils dictionary.

        Returns:
            dict: The non-forest soils dictionary.
        """
        return self.non_forest_soils
    
    def get_forest_type_keys(self):
        """
        Retrieves the forest type dictionary.

        Returns:
            dict: The forest type dictionary.
        """
        return self.forest_type_keys
    
    def get_soils_dict(self):
        """
        Retrieves the soils dictionary.

        Returns:
            dict: The soils dictionary.
        """
        return self.soils_dict
    
    def get_classifiers(self):
        """
        Retrieves the classifiers dictionary.

        Returns:
            dict: The classifiers dictionary.
        """
        return self.classifiers
    
    def get_disturbances_config(self):
        """
        Retrieves the disturbance ID dictionary for scenarios and baseline.

        Returns:
            dict: The disturbance ID dictionary.
        """
        return self.disturbances_config
    
    def get_yield_name_dict(self):
        """
        Retrieves the disturbance ID dictionary for scenarios and baseline.

        Returns:
            dict: The disturbance ID dictionary.
        """  
        return self.yield_name_dict
    
    def get_species_name_dict(self):
        """
        Get the dictionary mapping species IDs to their names.
        
        Returns:
            dict: A dictionary where the keys are species growth curve IDs and the values are species names.
        """
        return self.species_name_dict
    
    def get_afforestation_yield_name_dict(self):
        """
        Returns the dictionary containing the names of afforestation yield classes.
        
        Returns:
            dict: A dictionary containing the names of afforestation yield classes.
        """
        return self.afforestation_yield_name_dict
    
    def get_yield_baseline_dict(self):
        """
        Returns the yield baseline dictionary.

        Returns:
            dict: The yield baseline dictionary where keys are yield classes and values are the proportions of that yield class nationally.
        """
        return self.yield_baseline_dict
    
    def get_disturbance_cols(self):
        """
        Returns the disturbance columns used in the disturbance dataframe generator.

        Returns:
            list: A list of disturbance columns.
        """
        return self.disturbance_cols
    
    def get_static_disturbance_cols(self):
        """
        Returns the static disturbance columns used in the disturbance dataframe generator.

        Returns:
            list: A list of static disturbance columns.
        """
        return self.static_disturbance_cols
    
    def get_transition_cols(self):
        """
        Returns the transition columns used in the transition dataframe generator.

        Returns:
            list: A list of transition columns.
        """
        return self.transition_cols
    
    def get_mapping(self):
        """
        Returns the mapping used by the data manager to mapping parameters to the CBM AIDB.

        Returns:
            dict: The mapping used by the data manager.
        """
        return self.mapping
    
    def get_forest_baseline_year(self):
        """
        Get the forest baseline year, which is equal to the calibration year.

        Returns:
            int: The forest baseline year.
        """
        return self.forest_baseline_year
    
    def get_afforestation_baseline(self):
        """
        Returns the afforestation baseline, default is 1990.

        Returns:
            The afforestation baseline (1990).
        """
        return self.afforestation_baseline
    
    def get_scenario_data(self):
        """
        Returns the goblin scenario data, used to retrieve the harvest and thinning proportions for scenarios.
        
        Returns:
            dict: The scenario data.
        """
        return self.scenario_data

    def get_scenario_disturbance_dict(self):
        """
        Returns the scenario and baseline disturbance ID dictionary.

        Returns:
            dict: The scenario and baseline disturbance ID dictionary.
        """
        return self.scenario_disturbance_dict


    def get_config_data(self, config_file):
        """
        Load and return the configuration data from the specified file.

        Args:
            config_file (str): The path to the configuration file.

        Returns:
            dict: The configuration data loaded from the file.
        """
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)

        return config_data


    def gen_scenario_disturbance_dict(self, scenario_data):
        """
        Generate a dictionary of disturbance data for each scenario.

        Args:
            scenario_data (DataFrame): The input scenario data.

        Returns:
            dict: A dictionary containing disturbance data for each scenario.
        """
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
        """
        Get the baseline disturbance dictionary. This is added to the scenario disturbance dictionary.

        Args:
            scenario_dist (dict): The scenario disturbance dictionary.

        Returns:
            dict: The updated scenario disturbance dictionary with baseline disturbances.
        """
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
        """
        Get the legacy disturbance dictionary.

        Returns:
            dict: The legacy disturbance dictionary containing clearfell and thinning data.
        """
        clearfell = parser.get_clearfell_baseline(self.config_data)
        thinning = parser.get_thinning_baseline(self.config_data)

        legacy_dist = {}
        legacy_dist["DISTID1"] = clearfell
        legacy_dist["DISTID2"] = thinning

        return legacy_dist


