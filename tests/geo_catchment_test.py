from cbm_runner.geo_cbm_runner.catchment_forest_cover import CatchmentForest
from cbm_runner.resource_manager.scenario_data_fetcher import ScenarioDataFetcher
import os 
import pandas as pd

def main():
    path = "./data/geo_cbm_input"
    scenario_data = pd.read_csv(os.path.join(path, "scenario_input_dataframe.csv"))

    fetcher = ScenarioDataFetcher(scenario_data)
    catch = CatchmentForest()
    
    catchment = fetcher.get_catchment_name()
    print(catch.get_catchment_forest(catchment))

if __name__ == "__main__":
    main()