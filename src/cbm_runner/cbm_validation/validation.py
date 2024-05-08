"""
Validation Module 
=================
This module is responsible for the generation of validation data for specified SIT inputs. 
"""
import pandas as pd
import os

class ValidationData:
    """
    The ValidationData class is responsible for generating validation data for specified SIT inputs.
    """

    @staticmethod
    def gen_disturbance_statistics(object, years):
        """
        Gets disturbance statistics and returns a pandas dataframe.

        Args:
            object: An object containing the disturbance statistics data.
            years: The number of years of data.

        Returns:
            A pandas DataFrame containing the disturbance statistics data.
        """        

        data = pd.DataFrame()

        for year in range(1, years+1):
            if object.sit_event_stats_by_timestep[year] is not None:
                temp_data = object.sit_event_stats_by_timestep[year]
                temp_data["year"] = year

            data = pd.concat([data, temp_data], axis=0)

        
        # Set 'sit_event_index' as the index of the DataFrame
        if 'sit_event_index' in data.columns:
            data.set_index('sit_event_index', inplace=True)
        
        return data

    @staticmethod
    def gen_sit_events(object):
        """
        Gets SIT events data and saves it to a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            object: An object containing the SIT events data.
        """

        data = object.sit_events

        return data


    @staticmethod
    def gen_baseline_forest(output_data_path, data):
        """
        Saves baseline forest data to a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            data: The baseline forest data (pandas DataFrame).
        """

        data.to_csv(os.path.join(output_data_path, "scenario_baseline_forest.csv"))


    @staticmethod
    def merge_events(sit_events, events_data_by_timestep):
        """
        Merges SIT events and event statistics (by timestep) data and saves the 
        result as a CSV file.

        Args:
            output_data_path: The path to save the CSV file.

        """

        data_merge =[]

        for i in events_data_by_timestep.index:
            row = {"Species": sit_events.at[i, "Species"],
                   "Forest type": sit_events.at[i, "Forest_type"],
                   "Soil classes": sit_events.at[i, "Soil_classes"],
                   "Yield classes": sit_events.at[i, "Yield_classes"],
                   "Disturbance type": sit_events.at[i, "disturbance_type"],
                   "Year": sit_events.at[i, "time_step"],
                   "Target volume type": sit_events.at[i, "target_type"],
                   "Target volume": sit_events.at[i, "target"],
                   "Total eligible volume": events_data_by_timestep.at[i,"total_eligible_value"],
                   "Total volume achieved": events_data_by_timestep.at[i,"total_achieved"],
                   "Shortfall": events_data_by_timestep.at[i,"shortfall"],
                   "Shortfall bool": True if events_data_by_timestep.loc[i,"shortfall"] > 0.0 else False}
            data_merge.append(row)


        data = pd.DataFrame(data_merge)

        return data


    



        


        
  
        

        
    