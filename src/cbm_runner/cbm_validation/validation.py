"""
Validation Module 
=================
This module provides functions for clearing validation output folders, 
retrieving and saving validation data for different scenarios, and 
merging events data for analysis.
"""
import pandas as pd
import os

class ValidationData:
    """
    Provides static methods for working with validation data. 
    This includes clearing folders, saving/retrieving different types 
    of validation data, and merging events data.
    """
    @staticmethod
    def clear_validation_folder(output_data_path):
        """
        Clears the validation output folder.

        Args:
            output_data_path: The path to the validation output folder.
        """
        path = output_data_path.get_local_dir()

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path) and file != "__init__.py":  # Check if it's a file and not __init__.py
                os.remove(file_path)
    

    @staticmethod
    def gen_disturbance_statistics(output_data_path, object, years, sc):
        """
        Gets disturbance statistics and saves them to a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            object: An object containing the disturbance statistics data.
            years: The number of years of data.
            sc: The scenario identifier.
        """        

        data = pd.DataFrame()

        for year in range(1, years+1):
            if object.sit_event_stats_by_timestep[year] is not None:
                temp_data = object.sit_event_stats_by_timestep[year]
                temp_data["year"] = year

            data = pd.concat([data, temp_data], axis=0)

        
        data.to_csv(os.path.join(output_data_path, "scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv"))


    @staticmethod
    def gen_age_classes(output_data_path, object, sc):
        """
        Gets age class data and saves it to a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            object: An object containing the age class data.
            sc: The scenario identifier.
        """

        data = object.sit_data.age_classes

        data.to_csv(os.path.join(output_data_path, "scenario_" + str(sc) +"_age_classes.csv"))


    @staticmethod
    def gen_sit_events(object):
        """
        Gets SIT events data and saves it to a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            object: An object containing the SIT events data.
            sc: The scenario identifier.
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
    def merge_events(output_data_path, sc):
        """
        Merges SIT events and event statistics (by timestep) data and saves the 
        result as a CSV file.

        Args:
            output_data_path: The path to save the CSV file.
            sc: The scenario identifier.
        """

        events_names = pd.read_csv(os.path.join(output_data_path, "scenario_" + str(sc) +"_sit_events.csv"), index_col=0)
        events_data = pd.read_csv(os.path.join(output_data_path, "scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv"),index_col=7)

        data_merge =[]

        for i in events_data.index:
            row = {"Species": events_names.at[i, "Species"],
                   "Forest type": events_names.at[i, "Forest_type"],
                   "Soil classes": events_names.at[i, "Soil_classes"],
                   "Yield classes": events_names.at[i, "Yield_classes"],
                   "Disturbance type": events_names.at[i, "disturbance_type"],
                   "Year": events_names.at[i, "time_step"],
                   "Target volume type": events_names.at[i, "target_type"],
                   "Target volume": events_names.at[i, "target"],
                   "Total eligible volume": events_data.at[i,"total_eligible_value"],
                   "Total volume achieved": events_data.at[i,"total_achieved"],
                   "Shortfall": events_data.at[i,"shortfall"],
                   "Shortfall bool": True if events_data.loc[i,"shortfall"] > 0 else False}
            data_merge.append(row)


        data = pd.DataFrame(data_merge)

        data.to_csv(os.path.join(output_data_path, "scenario_"+str(sc)+"_linked_events.csv"))


    @staticmethod
    def results_contents(output_data_path, object, sc):
        """
        Saves various results data (area, flux, params, pools, state)
        as CSV files.

        Args:
            output_data_path: The path to save the CSV files.
            object: An object containing the results data.
            sc: The scenario identifier.
        """

        results= {
            "data_area":object.area,
            "data_flux":object.flux,
            "data_params":object.parameters,
            "data_pools":object.pools,
            "data_state":object.state}
        
        for key, data in results.items():
            results[key].to_csv(os.path.join(output_data_path, "scenario_" + str(sc) +"_results_" + key + ".csv"))


    @staticmethod
    def get_linked_events(path, sc):
        """
        Retrieves linked events data from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the linked events data, or an 
            error message if the file is not found.
        """
        try:
            data = pd.read_csv(os.path.join(path, "scenario_"+str(sc)+"_linked_events.csv"), index_col=0)
        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Linked events data file 'scenario_"+str(sc)+"_linked_events.csv' not found in the specified path."

        return data
    

    @staticmethod
    def get_site_event_stats_by_timestep(path, sc):
        """
        Retrieves site event stats by timestep data from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the site event stats by timestep data, or an
            error message if the file is not found.
        """
        try:
            data = pd.read_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv"), index_col=0)
        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Site event stats by timestep data file 'scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv' not found in the specified path."

        return data
    
    @staticmethod
    def get_age_classes(path, sc):
        """
        Retrieves age classes data from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the age classes data, or an
            error message if the file is not found.

        """
        try:
            data = pd.read_csv(os.path.join(path, "scenario_" + str(sc) +"_age_classes.csv"), index_col=0)
        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Age classes data file 'scenario_" + str(sc) +"_age_classes.csv' not found in the specified path."

        return data
    

    @staticmethod
    def get_sit_events(path, sc):
        """
        Retrieves SIT events data from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the SIT events data, or an
            error message if the file is not found.
        """
        try:
            data = pd.read_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_events.csv"), index_col=0)
        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Sit events data file 'scenario_" + str(sc) +"_sit_events.csv' not found in the specified path."

        return data
    

    @staticmethod
    def get_baseline_forest(path):
        """
        Retrieves baseline forest data from a CSV file.

        Args:
            path: The path to the CSV file.

        Returns:
            A pandas DataFrame containing the baseline forest data, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_baseline_forest.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Baseline forest data file 'scenario_baseline_forest.csv' not found in the specified path."

    @staticmethod
    def get_data_area(path, sc):
        """
        Retrieves data area results from a CSV file.
            
        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.
                    
        Returns:
            A pandas DataFrame containing the data area results, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_" + str(sc) +"_results_data_area.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Data area results file 'scenario_" + str(sc) +"_results_data_area.csv' not found in the specified path."
        

    @staticmethod
    def get_data_flux(path, sc):
        """
        Retrieves data flux results from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the data flux results, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_" + str(sc) +"_results_data_flux.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Data flux results file 'scenario_" + str(sc) +"_results_data_flux.csv' not found in the specified path."
        
    @staticmethod
    def get_data_params(path, sc):
        """
        Retrieves data params results from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the data params results, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_" + str(sc) +"_results_data_params.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Data params results file 'scenario_" + str(sc) +"_results_data_params.csv' not found in the specified path."
        
    
    @staticmethod
    def get_data_pools(path, sc):
        """
        Retrieves data pools results from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the data pools results, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_" + str(sc) +"_results_data_pools.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Data pools results file 'scenario_" + str(sc) +"_results_data_pools.csv' not found in the specified path."
        

    @staticmethod
    def get_data_state(path, sc):
        """
        Retrieves data state results from a CSV file.

        Args:
            path: The path to the CSV file.
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the data state results, or an
            error message if the file is not found.
        """
        file_path = os.path.join(path, "scenario_" + str(sc) +"_results_data_state.csv")

        try:
            data = pd.read_csv(file_path, index_col=0)
            return data

        except FileNotFoundError:
            # Handle the case where the file is not found 
            return "Error: Data state results file 'scenario_" + str(sc) +"_results_data_state.csv' not found in the specified path."
        
    