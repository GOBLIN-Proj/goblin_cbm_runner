"""
Database Manager Module
=======================
This module contains the class responsible for managing the database for the CBM Runner application.
"""
import sqlalchemy as sqa
import pandas as pd
from goblin_cbm_runner.database import get_local_dir
import os


class DataManager:
    """
    A class that manages the database for the CBM Runner application.

    Attributes:
        database_dir (str): The directory where the database is located.
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine used to connect to the database.

    Methods:
        data_engine_creater: Creates and returns the SQLAlchemy engine for connecting to the database.
        get_forest_inventory_age_strucuture: Retrieves the forest inventory age structure data from the database.
        get_forest_cbm_yields: Retrieves the forest CBM yields data from the database.
        get_forest_kb_yields: Retrieves the forest KB yields data from the database.
        get_NIR_forest_data_ha: Retrieves the NIR forest data in hectares from the database.
        get_cso_species_breakdown: Retrieves the CSO species breakdown data from the database.
        get_afforestation_areas_NIR: Retrieves the afforestation areas in NIR from the database.
        get_afforestation_areas_KB: Retrieves the afforestation areas in KB from the database.
        get_forest_harvest_NIR: Retrieves the forest harvest data in NIR from the database.
        get_kb_yield_curves: Retrieves the KB yield curves data from the database.
        get_disturbance_types: Retrieves the disturbance types data from the database.
        get_disturbance_times: Retrieves the disturbance times data from the database.
        get_disturbance_data: Retrieves the disturbance data from the database.
        get_baseline_classifiers: Retrieves the baseline classifiers from the database.
        get_baseline_age_classes: Retrieves the baseline age classes from the database.
        get_baseline_disturbance_events: Retrieves the baseline disturbance events from the database.
        get_baseline_disturbance_types: Retrieves the baseline disturbance types from the database.
        get_baseline_growth_curves: Retrieves the baseline growth curves from the database.
        get_baseline_inventory: Retrieves the baseline inventory from the database.
        get_baseline_transition: Retrieves the baseline transition from the database.
        get_baseline_standing_volume: Retrieves the baseline standing volume from the database.
        get_geo_baseline_standing_volume: Retrieves the baseline standing volume from the database.

    """

    def __init__(self):
        self.database_dir = get_local_dir()
        self.engine = self.data_engine_creater()

    def data_engine_creater(self):
        """
        Creates and returns a SQLAlchemy engine for the CBM Runner database.

        Returns:
            sqlalchemy.engine.Engine: The SQLAlchemy engine object.
        """
        database_path = os.path.abspath(
            os.path.join(self.database_dir, "cbm_runner_database.db")
        )
        engine_url = f"sqlite:///{database_path}"

        return sqa.create_engine(engine_url)

    def get_forest_inventory_age_strucuture(self):
        """
        Retrieves the age structure of the national forest inventory from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the age structure data.
        """
        table = "national_forest_inventory_2017"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_forest_cbm_yields(self):
        """
        Retrieves forest CBM yields from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the forest CBM yields.
        """
        table = "NIR_CBM_YIELD_Parameters"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_forest_kb_yields(self):
        """
        Retrieves the forest Firs yield parameters from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the yield parameters.
        """
        table = "NIR_KB_YIELD_Parameters"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_NIR_forest_data_ha(self):
        """
        Retrieves NIR (National Inventory Report) forest data in hectares from the database.

        Returns:
            pandas.DataFrame: The NIR forest data in hectares.
        """
        
        table = "forest_data"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["year"]
        )

        dataframe *= 1000

        return dataframe

    def get_cso_species_breakdown(self):
        """
        Retrieves the CSO species breakdown data from the database.

        Returns:
            pandas.DataFrame: The CSO species breakdown data.
        """
        # CSO data is from 2007 onward. Additional data added from NFI from 1998 to 2006.
        # Data from 1991 is based on 1998 breakdown.

        table = "cso_afforestation_species_proportion"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["year"]
        )

        return dataframe

    def get_afforestation_areas_NIR(self):
        """
        Retrieves afforestation areas data from the (National Inventory Report)'afforestation_NIR' table in the database.
        
        Returns:
            pandas.DataFrame: The afforestation areas data with the year as the index.
        """
        
        table = "afforestation_NIR"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["year"]
        )

        dataframe *= 1000

        return dataframe

    def get_afforestation_areas_KB(self):
        """
        Retrieves the afforestation areas from the (Firs) KB_Afforestation_Area table in the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the afforestation areas, with the year as the index.
        """
        table = "KB_Afforestation_Area"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["year"]
        )

        return dataframe

    def get_forest_harvest_NIR(self):
        """
        Retrieves the forest harvest National Invetory Report data from the database.

        Returns:
            pandas.DataFrame: The forest harvest NIR data.
        """
        table = "forest_harvest_NIR"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["year"]
        )

        return dataframe

    def get_kb_yield_curves(self):
        """
        Retrieve the Firs yield curves from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the Firs yield curves data.
        """
        table = "KB_yield_curves"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["Cohort"]
        )

        return dataframe

    def get_disturbance_types(self):
        """
        Retrieves all disturbance types from the 'Disturbances' table in the database.

        Returns:
            pandas.DataFrame: A DataFrame containing all disturbance types.
        """
        table = "Disturbances"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_disturbance_times(self):
        """
        Retrieves disturbance timing data from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing disturbance timing data.
        """
        table = "Disturbance_timing"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["Cohort"]
        )

        return dataframe

    def get_disturbance_data(self):
        """
        Retrieves the Firs disturbance data from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the disturbance data.
        """
        table = "KB_Disturbance_data_original"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_baseline_classifiers(self):
        """
        Retrieves the baseline classifiers from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline classifiers.
        """
        table = "base_classifiers_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_age_classes(self):
        """
        Retrieves the baseline age classes from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline age classes.
        """
        table = "base_age_class_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_disturbance_events(self):
        """
        Retrieves the baseline disturbance events from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline disturbance events.
        """
        table = "base_disturbance_events_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_disturbance_types(self):
        """
        Retrieves the baseline disturbance types from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline disturbance types.
        """
        table = "base_disturbance_types_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_growth_curves(self):
        """
        Retrieves the baseline growth curves from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline growth curves.
        """
        table = "base_growth_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_inventory(self):
        """
        Retrieves the baseline inventory from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline inventory.
        """
        table = "base_inventory_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_transition(self):
        """
        Retrieves the baseline transition from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline transition.
        """
        table = "base_transition_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe
    
    def get_baseline_standing_volume(self):
        """
        Retrieves the baseline standing volume from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline standing volume.
        """
        table = "base_standing_volume_2016_to_2050"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table),
            self.engine,
        )

        return dataframe

    def get_geo_baseline_standing_volume(self):
        """
        Retrieves the baseline standing volume from the database.

        Returns:
            pandas.DataFrame: A DataFrame containing the baseline standing volume.
        """
        table = "kb_geo_standing_vol"
        dataframe = pd.read_sql(
            "SELECT * FROM '%s'" % (table), self.engine, index_col=["Cohort"]
        )

        return dataframe