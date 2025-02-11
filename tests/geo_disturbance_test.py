from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_FM_disturbances import FMDisturbances
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_SC_disturbances import SCDisturbances
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
import pandas as pd
import os

def main():
    path = "./data/geo_cbm_input"
    results_path = "./data/dist_test_results"

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "geo_cbm_afforestation.csv"), index_col=0
    )

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_input_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020

    #forest_end_year = 2050

    # geo_data_manager
    geo_data_manager = GeoDataManager(
        calibration_year = calibration_year, 
        config_file_path = config, 
        scenario_data = sc_data, 
        afforest_data = afforest_data, 
        sit_path = None)
    

    fm_disturbances = FMDisturbances(geo_data_manager)

    # test FM_forest_disturbances

    fm_disturbances.fill_baseline_forest().to_csv(os.path.join(results_path, "geo_FM_disturbances.csv"), index=False)
    print("finished FM disturbance test")

    
    af_disturbances = SCDisturbances(geo_data_manager)

    # test AF_forest_disturbances
    af_disturbances.fill_scenario_forest(0).to_csv(os.path.join(results_path, "geo_AF_disturbances.csv"), index=False)

    print("finished AF disturbance test")


if __name__ == "__main__":
    main()
    