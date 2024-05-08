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
        forest_kb_yields: Returns the forest Firs yields dataframe.
        NIR_forest_data_ha: Returns the NIR forest data (hectares) dataframe.
        cso_species_breakdown: Returns the CSO species breakdown dataframe.
        afforestation_areas_NIR: Returns the afforestation areas (NIR) dataframe.
        afforestation_areas_KB: Returns the afforestation areas (Firs) dataframe.
        disturbance_time: Returns the disturbance times dataframe.
        kb_yield_curves: Returns the Firs yield curves dataframe.
        disturbance_type: Returns the disturbance types dataframe.
        harvest_areas_NIR: Returns the forest harvest areas (NIR) dataframe.
        disturbance_data: Returns the disturbance data dataframe.
        base_age_class: Returns the baseline (2016 - 2050) age class dataframe.
        base_classifiers: Returns the baseline (2016 - 2050) classifiers dataframe.
        base_disturbance_events: Returns the baseline (2016 - 2050) disturbance events dataframe.
        base_disturbance_types: Returns the baseline (2016 - 2050) disturbance types dataframe.
        base_growth_curves: Returns the baseline (2016 - 2050) growth curves dataframe.
        base_inventory: Returns the baseline (2016 - 2050) inventory dataframe.
        base_transition: Returns the baseline (2016 - 2050) transitions dataframe.
        base_standing_volume: Returns the baseline (2016 - 2050) standing volume dataframe.
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

    def afforestation_areas_KB(self):
        """
        Returns the afforestation areas (KB) dataframe.
        """
        return self.dataframes.get_afforestation_areas_KB()

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

    def disturbance_data(self):
        """
        Returns the disturbance data dataframe.
        """
        return self.dataframes.get_disturbance_data()
    
    def base_age_class(self):
        """
        Returns the baseline (2016 - 2050) age class dataframe.
        """
        return self.dataframes.get_baseline_age_classes()
    
    def base_classifiers(self):
        """
        Returns the baseline (2016 - 2050) classifiers dataframe.
        """
        return self.dataframes.get_baseline_classifiers()
    
    def base_disturbance_events(self):
        """
        Returns the baseline (2016 - 2050) disturbance events dataframe.
        """
        return self.dataframes.get_baseline_disturbance_events()
    
    def base_disturbance_types(self):
        """
        Returns the baseline (2016 - 2050) disturbance types dataframe.
        """
        return self.dataframes.get_baseline_disturbance_types()
    
    def base_growth_curves(self):
        """
        Returns the baseline (2016 - 2050) growth curves dataframe.
        """
        return self.dataframes.get_baseline_growth_curves()
    
    def base_inventory(self):
        """
        Returns the baseline (2016 - 2050) inventory dataframe.
        """
        return self.dataframes.get_baseline_inventory()
    
    def base_transition(self):
        """
        Returns the baseline (2016 - 2050) transitions dataframe.
        """
        return self.dataframes.get_baseline_transition()
    
    def base_standing_volume(self):
        """
        Returns the baseline (2016 - 2050) standing volume dataframe.
        """
        return self.dataframes.get_baseline_standing_volume()
