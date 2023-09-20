from cbm_runner.database_manager import DataManager



class Loader:
    def __init__(self):
        self.dataframes = DataManager()


    def forest_age_structure(self):
        return self.dataframes.get_forest_inventory_age_strucuture()
    
    def forest_cbm_yields(self):
        return self.dataframes.get_forest_cbm_yields()
    
    def forest_kb_yields(self):
        return self.dataframes.get_forest_kb_yields()
    
    
    def NIR_forest_data_ha(self):
        return self.dataframes.get_NIR_forest_data_ha()


    def afforesation_species_breakdown(self):
        return self.dataframes.get_afforesation_species_breakdown()
    

    def afforesation_areas_NIR(self):
        return self.dataframes.get_afforesation_areas_NIR()


    def harvest_areas_NIR(self):
        return self.dataframes.get_forest_harvest_NIR()
