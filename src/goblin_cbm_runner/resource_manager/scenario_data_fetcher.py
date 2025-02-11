"""
Scenario Data Fetcher
=====================

The `ScenarioDataFetcher` class extracts specific pieces of information from a scenario dataset.
"""

class ScenarioDataFetcher:
   """
   Extracts specific pieces of information from a scenario dataset.

   Methods:
      __init__(geo_data_manager):
         Initializes an instance of the `ScenarioDataFetcher` class.
         
      get_column_index(column_name):
         Retrieves the index of a specified column in the scenario data.
         
      get_afforestation_end_year():
         Retrieves the end year for afforestation activities.
         
      get_catchment_name():
         Retrieves the name of the catchment area.
         
      get_scenario_list():
         Retrieves a list of all scenarios.
         
      get_afforest_scenario_index():
         Retrieves a list of afforestation scenario indices.
   """
   def __init__(self, geo_data_manager):
      self.scenario_data = geo_data_manager.get_scenario_data()
    
   def get_column_index(self, column_name):
      """
      Retrieves the index of a specified column in the scenario data.

      Args:
         column_name (str): The name of the column.

      Returns:
         int: The index of the column, or None if not found.
      """
      lower_case_columns = [col.lower() for col in self.scenario_data.columns]
      try:
         column_index = lower_case_columns.index(column_name)
         return column_index
      except ValueError:
         return None

   def get_afforestation_end_year(self):
      """
      Retrieves the end year for afforestation activities.

      Returns:
         int: The afforestation end year.
      """
      column_index = self.get_column_index("afforest year")
      matching_column_name = self.scenario_data.columns[column_index]
      return self.scenario_data[matching_column_name].unique().item()
   
   def get_catchment_name(self):
      """
      Retrieves the name of the catchment area.

      Returns:
         str: The catchment name.
      """
      column_index = self.get_column_index("catchment")
      matching_column_name = self.scenario_data.columns[column_index]
      return self.scenario_data[matching_column_name].unique().item()

   def get_scenario_list(self):
      """
      Retrieves a list of all scenarios.

      Returns:
         list: A list of scenario identifiers.
      """
      column_index = self.get_column_index("scenarios")
      matching_column_name = self.scenario_data.columns[column_index]
      return self.scenario_data[matching_column_name].unique().tolist()
    
   def get_afforest_scenario_index(self):
      """
      Retrieves a list of afforestation scenario indices.

      Returns:
         list: A list containing -1 followed by all scenario indices.
      """
      scenarios = [-1]
      scenarios.extend(self.get_scenario_list())
      return scenarios

