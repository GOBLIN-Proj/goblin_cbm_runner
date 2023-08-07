import sqlalchemy as sqa
import pandas as pd
from cbm_runner.database import get_local_dir
import os


class DataManager:
    def __init__(self):
        self.database_dir = get_local_dir()
        self.engine = self.data_engine_creater()

    def data_engine_creater(self):
        database_path = os.path.abspath(
            os.path.join(self.database_dir, "cbm_runner_database.db")
        )
        engine_url = f"sqlite:///{database_path}"

        return sqa.create_engine(engine_url)
    
    

    def get_forest_inventory_age_strucuture(self):
        table = "national_forest_inventory_2017"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )
        
        return dataframe

    def get_forest_cbm_yields(self):
        table = "NIR_CBM_YIELD_Parameters"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )
        
        return dataframe
    
    def get_forest_kb_yields(self):
        table = "NIR_KB_YIELD_Parameters"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )
        
        return dataframe
    
    def get_NIR_forest_data_ha(self):
        table = "forest_data"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
            index_col =["year"]
        )
        
        dataframe *= 1000

        return dataframe
    
    def get_afforesation_species_breakdown(self):
        #CSO data is from 2007 onward. Addtional data added from NFI from 1998 to 2006. 
        #Data from 1991 is based on 1998 breakdown.
        
        table = "cso_afforestation_species_proportion"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
            index_col =["year"]
        )
        
        return dataframe


    def get_afforesation_areas_NIR(self):
        table = "afforestation_NIR"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
            index_col =["year"]
        )
        
        dataframe *= 1000

        return dataframe
