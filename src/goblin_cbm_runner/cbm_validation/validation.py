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
        dist_dict = {"DISTID4": "Afforestation", "DISTID2": "Thinning", "DISTID1": "Clearcut", "DISTID3": "Fire"}
        data_merge =[]

        for i in events_data_by_timestep.index:
            row = {"Species": sit_events.at[i, "Species"],
                   "Forest type": sit_events.at[i, "Forest_type"],
                   "Soil classes": sit_events.at[i, "Soil_classes"],
                   "Yield classes": sit_events.at[i, "Yield_classes"],
                   "Disturbance type": dist_dict[sit_events.at[i, "disturbance_type"]],
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
    

    @staticmethod
    def merge_FM_events(sit_events, events_data_by_timestep):
        """
        Merges SIT events and event statistics (by timestep) data and saves the 
        result as a CSV file.

        Args:
            output_data_path: The path to save the CSV file.

        """
        dist_dict = {"DISTID4": "Afforestation", "DISTID2": "Thinning", "DISTID1": "Clearcut", "DISTID3": "Fire"}
        data_merge =[]

        for i in events_data_by_timestep.index:
            row = {"Climate Unit": sit_events.at[i, "Climate_unit"],
                   "Forest type": sit_events.at[i, "Forest_management_types"],
                   "Species": sit_events.at[i, "Species"],
                   "Yield classes": sit_events.at[i, "Yield_classes"],
                   "Disturbance type": dist_dict[sit_events.at[i, "disturbance_type"]],
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
    
    @staticmethod
    def merge_disturbances_and_parse(stocks, time_step_params):
        """
        Merges disturbance and stock data and parses the result.

        Args:
            stocks: The stocks data.
            disturbances: The disturbances data.

        Returns:
            A pandas DataFrame containing the merged and parsed data.
        """
        disturbances = ["Afforestation","Thinning","Clearcut"]
        data_merge = []

        for i in time_step_params.index:
            if time_step_params.at[i,"disturbance_type"] in disturbances:

                row = {"Species": stocks.at[i, "Species"],
                       "Forest type": stocks.at[i, "Forest_type"],
                        "Soil classes": stocks.at[i, "Soil_classes"],
                        "Yield classes": stocks.at[i, "Yield_classes"],
                        "Disturbance type": time_step_params.at[i,"disturbance_type"],
                        "Year": stocks.at[i,"timestep"] + 1989,
                        "Area": stocks.at[i,"Input"],}

                data_merge.append(row)

        return pd.DataFrame(data_merge).groupby(["Species", "Forest type", "Soil classes", "Yield classes", "Year","Disturbance type"]).sum().sort_values(by=["Year"])


    
    @staticmethod
    def FM_merge_baseline_disturbances_and_parse(stocks, time_step_params):
        """
        Merges disturbance and stock data and parses the result.

        Args:
            stocks: The stocks data.
            disturbances: The disturbances data.

        Returns:
            A pandas DataFrame containing the merged and parsed data.
        """
        disturbances = [1,2]
        data_merge = []

        for i in time_step_params.index:
            if time_step_params.at[i,"disturbance_type"] in disturbances:

                row = {"Climate unit": stocks.at[i, "Climate_unit"],
                       "Forest management types": stocks.at[i, "Forest_management_types"],
                        "Species": stocks.at[i, "Species"],
                        "Yield classes": stocks.at[i, "Yield_classes"],
                        "Disturbance type": time_step_params.at[i,"disturbance_type"],
                        "Year": stocks.at[i,"timestep"],
                        "Area": stocks.at[i,"Input"],}

                data_merge.append(row)

        return pd.DataFrame(data_merge).groupby(["Climate unit", "Forest management types", "Species", "Yield classes", "Year","Disturbance type"]).sum().sort_values(by=["Year"])


    @staticmethod
    def default_merge_disturbances_and_parse(stocks, time_step_params):
        """
        Merges disturbance and stock data and parses the result.

        Args:
            stocks: The stocks data.
            disturbances: The disturbances data.

        Returns:
            A pandas DataFrame containing the merged and parsed data.
        """
        disturbances = ["Afforestation","Thinning","Clearcut"]
        data_merge = []

        for i in time_step_params.index:
            if time_step_params.at[i,"disturbance_type"] in disturbances:

                row = {"Species": stocks.at[i, "Species"],
                       "Forest type": stocks.at[i, "Forest_type"],
                        "Soil classes": stocks.at[i, "Soil_classes"],
                        "Yield classes": stocks.at[i, "Yield_classes"],
                        "Disturbance type": time_step_params.at[i,"disturbance_type"],
                        "Year": stocks.at[i,"timestep"],
                        "Area": stocks.at[i,"Input"],}

                data_merge.append(row)

        return pd.DataFrame(data_merge).groupby(["Species", "Forest type", "Soil classes", "Yield classes", "Year","Disturbance type"]).sum().sort_values(by=["Year"])


    @staticmethod
    def disturbance_summary(stocks, time_step_params):
        data = ValidationData.default_merge_disturbances_and_parse(stocks, time_step_params)
        pivot_table = data.pivot_table(
            values='Area', 
            index=['Species', 'Forest type', 'Soil classes', 'Yield classes', 'Year'], 
            columns='Disturbance type', 
            aggfunc='sum', 
            fill_value=0
        )
        return pivot_table
    