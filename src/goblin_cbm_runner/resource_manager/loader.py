"""
Loader
======
The Loader class is responsible for loading various dataframes used in the CBM Runner.
"""
from goblin_cbm_runner.resource_manager.database_manager import DataManager

class Loader:
    """
    The Loader class is responsible for loading various dataframes used in the CBM Runner.

    Attributes:
        dataframes (DataManager): An instance of the DataManager class for managing the dataframes.

    Methods:
        forest_age_structure: Returns the forest inventory age structure dataframe.
        forest_cbm_yields: Returns the forest CBM yields dataframe.
        forest_kb_yields: Returns the forest KB yields dataframe.
        NIR_forest_data_ha: Returns the NIR forest data (hectares) dataframe.
        cso_species_breakdown: Returns the CSO species breakdown dataframe.
        afforestation_areas_NIR: Returns the afforestation areas (NIR) dataframe.
        disturbance_time: Returns the disturbance times dataframe.
        kb_yield_curves: Returns the KB yield curves dataframe.
        kb_standing_vol_yield_curves: Returns the KB standing volume yield curves dataframe.
        disturbance_type: Returns the disturbance types dataframe.
        harvest_areas_NIR: Returns the forest harvest areas (NIR) dataframe.
        FM_age_class: Returns the managed forest age class dataframe.
        FM_classifiers: Returns the managed forest classifiers dataframe.
        FM_disturbance_types: Returns the managed forest disturbance types dataframe.
        FM_growth_curves: Returns the managed forest growth curves dataframe.
        FM_inventory: Returns the managed forest inventory dataframe.
        FM_transition: Returns the managed forest transitions dataframe.
        FM_standing_volume: Returns the managed forest standing volume dataframe.
        FM_disturbances_time_series: Returns the managed forest disturbances time series dataframe.
        AF_disturbances_time_series: Returns the historic afforestation disturbances time series dataframe.
        AF_age_class: Returns the historic afforestation age class dataframe.
        AF_classifiers: Returns the historic afforestation classifiers dataframe.
        AF_disturbance_types: Returns the historic afforestation disturbance types dataframe.
        AF_growth_curves: Returns the historic afforestation growth curves dataframe.
        AF_inventory: Returns the historic afforestation inventory dataframe.
        AF_transition: Returns the historic afforestation transitions dataframe.
    """

    def __init__(self):
        self.dataframes = DataManager()

    def forest_age_structure(self):
        """
        Returns the forest inventory age structure dataframe.
        """
        return self.dataframes.get_forest_inventory_age_strucuture()

    def forest_cbm_yields(self):
        """
        Returns the forest CBM yields dataframe.
        """
        return self.dataframes.get_forest_cbm_yields()

    def forest_kb_yields(self):
        """
        Returns the forest KB yields dataframe.
        """
        return self.dataframes.get_forest_kb_yields()
    
    def NIR_forest_data_ha(self):
        """
        Returns the NIR forest data (hectares) dataframe.
        """
        return self.dataframes.get_NIR_forest_data_ha()

    def cso_species_breakdown(self):
        """
        Returns the CSO species breakdown dataframe.
        """
        return self.dataframes.get_cso_species_breakdown()

    def afforestation_areas_NIR(self):
        """
        Returns the afforestation areas (NIR) dataframe.
        """
        return self.dataframes.get_afforestation_areas_NIR()

    def disturbance_time(self):
        """
        Returns the disturbance times dataframe.
        """
        return self.dataframes.get_disturbance_times()

    def kb_yield_curves(self):
        """
        Returns the KB yield curves dataframe.
        """
        return self.dataframes.get_kb_yield_curves()
    
    def kb_standing_vol_yield_curves(self):
        """
        Returns the KB standing volume yield curves dataframe.
        """
        return self.dataframes.get_geo_baseline_standing_volume()

    def disturbance_type(self):
        """
        Returns the disturbance types dataframe.
        """
        return self.dataframes.get_disturbance_types()

    def harvest_areas_NIR(self):
        """
        Returns the forest harvest areas (NIR) dataframe.
        """
        return self.dataframes.get_forest_harvest_NIR()

    def FM_age_class(self):
        """
        Returns the managed forest age class dataframe.
        """
        return self.dataframes.get_FM_age_classes()
    
    def FM_classifiers(self):
        """
        Returns the managed forest classifiers dataframe.
        """
        return self.dataframes.get_FM_classifiers()

    def FM_disturbance_types(self):
        """
        Returns the managed forest disturbance types dataframe.
        """
        return self.dataframes.get_FM_disturbance_types()
    
    def FM_growth_curves(self):
        """
        Returns the managed forest growth curves dataframe.
        """
        return self.dataframes.get_FM_growth_curves()
    
    def FM_inventory(self):
        """
        Returns the managed forest inventory dataframe.
        """
        return self.dataframes.get_FM_inventory()
    
    def FM_transition(self):
        """
        Returns the managed forest transitions dataframe.
        """
        return self.dataframes.get_FM_transition()
    
    def FM_standing_volume(self):
        """
        Returns the managed forest standing volume dataframe.
        """
        return self.dataframes.get_FM_standing_volume()

    def FM_disturbances_time_series(self, intensity="high"):
        """
        Returns the managed forest disturbances time series dataframe.
        
        Parameters:
        - intensity (str): The intensity level of disturbances ("low", "high").
        
        Returns:
        - pandas.DataFrame: Time series of forest disturbances.
        """
        valid_intensities = {"low", "high"}

        intensity = intensity.lower()
        
        if intensity not in valid_intensities:
            raise ValueError(f"Invalid intensity: {intensity}. Choose from {valid_intensities}.")
        
        return self.dataframes.get_FM_disturbance_events(intensity)

    
    def AF_disturbances_time_series(self, intensity="high"):
        """
        Returns the historic afforestation disturbances time series dataframe.
        
        Parameters:
        - intensity (str): The intensity level of disturbances ("low", "high").
        
        Returns:
        - pandas.DataFrame: Time series of forest disturbances.
        """
        valid_intensities = {"low", "high"}
        intensity = intensity.lower()
        
        if intensity not in valid_intensities:
            raise ValueError(f"Invalid intensity: {intensity}. Choose from {valid_intensities}.")
        
        return self.dataframes.get_AF_disturbance_events(intensity)

    def AF_age_class(self):
        """
        Returns the historic afforestation age class dataframe.
        """
        return self.dataframes.get_AF_age_classes()
    
    def AF_classifiers(self):
        """
        Returns the historic afforestation classifiers dataframe.
        """
        return self.dataframes.get_AF_classifiers()
    
    def AF_disturbance_types(self):
        """
        Returns the historic afforestation disturbance types dataframe.
        """
        return self.dataframes.get_AF_disturbance_types()
    
    def AF_growth_curves(self):
        """
        Returns the historic afforestation growth curves dataframe.
        """
        return self.dataframes.get_AF_growth_curves()
    
    def AF_inventory(self):
        """
        Returns the historic afforestation inventory dataframe.
        """
        return self.dataframes.get_AF_inventory()
    
    def AF_transition(self):
        """
        Returns the historic afforestation transitions dataframe.
        """
        return self.dataframes.get_AF_transition()

