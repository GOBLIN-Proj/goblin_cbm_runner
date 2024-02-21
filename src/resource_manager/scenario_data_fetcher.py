"""
Scenario Data Fetcher Documentation
====================================

The ``ScenarioDataFetcher`` class is designed to extract specific pieces of information from a scenario dataset. 

"""
import pandas as pd

class ScenarioDataFetcher:
   """
   The ScenarioDataFetcher class is designed to extract specific pieces of information from a scenario dataset.

   This class provides methods to retrieve various information from a scenario dataset.

   Methods:
      __init__(scenario_data):
         Initializes an instance of the `ScenarioDataFetcher` class.
         
      get_column_index(column_name):
         Retrieves the index of a specified column in the scenario data.
         
      get_afforestation_end_year():
         Retrieves the end year for afforestation activities for a specified scenario.
         
      get_catchment_name():
         Retrieves the name of the catchment area defined in the scenario data.
         
      get_scenario_list():
         Retrieves a list of all scenarios present in the scenario data.
         
      get_afforest_scenario_index():
         Retrieves a list of afforestation scenario indices, with -1 indicating a special scenario, followed by the indices of all available scenarios.
   """
   def __init__(self, scenario_data):
      self.scenario_data = scenario_data
    

   def get_column_index(self, column_name):
      """
      Retrieves the index of a specified column in the scenario data.

      Args:
         column_name (str): The name of the column to retrieve.

      Returns:
         int: The index of the column.
      """
      lower_case_columns = [col.lower() for col in self.scenario_data.columns]
      try:
         column_index = lower_case_columns.index(column_name)
         return column_index
      
      except ValueError:

         return None
        

   def get_afforestation_end_year(self):
      """
      Retrieves the end year for afforestation activities for a specified scenario.

      Returns:
         int: The afforestation end year.
      """
      column_index = self.get_column_index("afforest year")

      matching_column_name = self.scenario_data.columns[column_index]

      return self.scenario_data[matching_column_name].unique().item()
   
    
   def get_catchment_name(self):
      """
      Retrieves the name of the catchment area defined in the scenario data.

      Returns:
         str: The catchment name.
      """
      column_index = self.get_column_index("catchment")
      matching_column_name = self.scenario_data.columns[column_index]

      return self.scenario_data[matching_column_name].unique().item()

    
   def get_scenario_list(self):
      """
      Retrieves a list of all scenarios present in the scenario data.

      Returns:
         list: A list of scenario identifiers.
      """
      column_index = self.get_column_index("scenarios")
      matching_column_name = self.scenario_data.columns[column_index]

      return self.scenario_data[matching_column_name].unique().tolist()
    
   def get_afforest_scenario_index(self):
        
      """
      Retrieves a list of afforestation scenario indices, with -1 indicating a special scenario,
      followed by the indices of all available scenarios.

      Returns:
         list: A list containing -1 followed by all scenario indices.
      """
      # Create a list with -1 as the first element
      scenarios = [-1]
      # Extend the list with the scenario indices obtained from get_scenario_list method
      scenarios.extend(self.get_scenario_list())
      
      return scenarios
         
