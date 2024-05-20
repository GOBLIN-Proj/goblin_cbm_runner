"""
Catchment Forest Cover Module
==============================

This module provides functionalities to analyze and process forest cover data within specific catchments.
It leverages external API services to fetch the required data and applies various data processing techniques
to filter, aggregate, and present the catchment forest data in a structured format.

Classes:
    CatchmentForest: Manages the retrieval and transformation of forest cover data for catchments.

Dependencies:
    catchment_data_api.catchment_data_api.CatchmentDataAPI: External API service class for fetching catchment data.
    pandas: Library for data manipulation and analysis.
"""

from catchment_data_api.catchment_data_api import CatchmentDataAPI
import pandas as pd 


class CatchmentForest:
    """
    A class to manage and process forest cover data for given catchment areas.

    Attributes:
        api (CatchmentDataAPI): An instance of the CatchmentDataAPI class for accessing catchment data.
    
    Methods:
        get_catchment_forest(catchment):
            Retrieves and processes forest cover data for a specified catchment area.
    """
    def __init__(self):
        self.api = CatchmentDataAPI()


    def get_catchment_forest(self, catchment):
        """
        Retrieves and processes forest cover data for a specified catchment area.

        This method fetches raw forest cover data using the CatchmentDataAPI, filters the data 
        for specific forest types, applies mappings for cover and soil types, and aggregates the 
        data by catchment, forest type, and soil type. The resulting data is then pivoted to present 
        soil types as columns, providing a structured view of the total hectares covered by each 
        forest type and soil type within the catchment.

        Args:
            catchment (str): The name of the catchment area for which forest cover data is to be retrieved.

        Returns:
            pandas.DataFrame: A DataFrame containing aggregated forest cover data for the specified catchment,
            structured by forest species, with columns for different soil types and their corresponding
            total hectares.
        """
        forest_df = self.api.get_catchment_forest_data_by_catchment_name(catchment)

        # Filter for specific types of forests and then group
        forest_types = ['Broadleaved Forest and Woodland', 'Coniferous Forest', 'Mixed Forest', 'Transitional Forest']
        filtered_df = forest_df[forest_df['cover_type'].isin(forest_types)].copy()

        # Mapping for cover_type and soil_type
        cover_type_mapping = {
            'Mixed Forest': 'CBmix',
            'Coniferous Forest': 'Sitka',
            'Broadleaved Forest and Woodland': 'SGB',
            'Transitional Forest': 'CBmix'
        }

        soil_type_mapping = {
            'mineral': 'mineral',
            'misc': 'mineral',
            'peaty_mineral': 'peat',
            'peat': 'peat'
        }

        # Apply mappings
        filtered_df.loc[:, 'cover_type'] = filtered_df['cover_type'].replace(cover_type_mapping)
        filtered_df.loc[:, 'soil_type'] = filtered_df['soil_type'].replace(soil_type_mapping)

        # Aggregate data by catchment, cover_type, and soil_type, summing total_hectares
        aggregated_df = filtered_df.groupby(['catchment', 'cover_type', 'soil_type'], as_index=False)['total_hectares'].sum()

        # Pivot to get soil types as columns
        pivot_df = aggregated_df.pivot_table(index=['catchment', 'cover_type'], columns='soil_type', values='total_hectares', fill_value=0)

        # Reset index to make 'catchment' and 'cover_type' back to columns and rename columns
        pivot_df.reset_index(inplace=True)
        pivot_df.columns.name = None  # Remove the name of the columns axis
        pivot_df = pivot_df.rename(columns={'cover_type': 'species', 'Peat': 'peat', 'Mineral': 'mineral'})

        # Select only the required columns
        final_df = pivot_df[['species', 'peat', 'mineral']]
 
        return final_df