import cbm_runner.validation_data as output_data_path
import pandas as pd
import os

class ValidationData:

    @staticmethod
    def clear_validation_folder():
        path = output_data_path.get_local_dir()

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path) and file != "__init__.py":  # Check if it's a file and not __init__.py
                os.remove(file_path)
    

    @staticmethod
    def get_disturbance_statistics(object, years, sc):
        path = output_data_path.get_local_dir()

        data = pd.DataFrame()
        for year in range(1, years+1):
            temp_data = object.sit_event_stats_by_timestep[year]
            temp_data["year"] = year

            data = pd.concat([data, temp_data], axis=0)

        
        data.to_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv"))


    @staticmethod
    def get_age_classes(object, sc):
        path = output_data_path.get_local_dir()

        data = object.sit_data.age_classes

        data.to_csv(os.path.join(path, "scenario_" + str(sc) +"_age_classes.csv"))


    @staticmethod
    def get_sit_events(object, sc):
        path = output_data_path.get_local_dir()

        data = object.sit_events

        data.to_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_events.csv"))