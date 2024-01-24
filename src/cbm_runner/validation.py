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


    @staticmethod
    def get_baseline_forest(data):
        path = output_data_path.get_local_dir()

        data.to_csv(os.path.join(path, "scenario_baseline_forest.csv"))


    @staticmethod
    def merge_events(sc):
        path = output_data_path.get_local_dir()

        events_names = pd.read_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_events.csv"), index_col=0)
        events_data = pd.read_csv(os.path.join(path, "scenario_" + str(sc) +"_sit_event_stats_by_timestep.csv"),index_col=7)

        data_merge =[]

        for i in events_data.index:
            row = {"Species": events_names.at[i, "Species"],
                   "Forest type": events_names.at[i, "Forest type"],
                   "Soil classes": events_names.at[i, "Soil classes"],
                   "Yield classes": events_names.at[i, "Yield classes"],
                   "Year": events_names.at[i, "time_step"],
                   "Target volume type": events_names.at[i, "target_type"],
                   "Target volume": events_names.at[i, "target"],
                   "Total eligible volume": events_data.at[i,"total_eligible_value"],
                   "Total volume achieved": events_data.at[i,"total_achieved"],
                   "Shortfall": events_data.at[i,"shortfall"],
                   "Shortfall bool": True if events_data.loc[i,"shortfall"] > 0 else False}
            data_merge.append(row)


        data = pd.DataFrame(data_merge)

        data.to_csv(os.path.join(path, "scenario_"+str(sc)+"_linked_events.csv"))

