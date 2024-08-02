from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_FM_disturbances import FMDisturbances
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

    forest_end_year = 2050

    fm_disturbances = FMDisturbances(config, calibration_year, forest_end_year, afforest_data, sc_data)

    fm_disturbances.fill_baseline_forest().to_csv(os.path.join(results_path, "geo_FM_disturbances.csv"), index=False)
    print("finished FM disturbance test")





if __name__ == "__main__":
    main()
    