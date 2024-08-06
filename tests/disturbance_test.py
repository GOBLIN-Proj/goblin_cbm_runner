from goblin_cbm_runner.cbm.AF_disturbances import AFDisturbances
from goblin_cbm_runner.cbm.SC_disturbances import SCDisturbances
import pandas as pd
import os

def main():
    path = "./data/runner_input"
    results_path = "./data/dist_test_results"

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "cbm_afforestation.csv"), index_col=0
    )


    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020

    forest_end_year = 2100

    af_disturbances = AFDisturbances(config, calibration_year, forest_end_year, afforest_data, sc_data)

    af_disturbances.fill_baseline_forest().to_csv(os.path.join(results_path, "af_disturbances.csv"), index=False)
    print("finished AF disturbance test")

    sc_disturbances = SCDisturbances(config, calibration_year, forest_end_year, afforest_data, sc_data)

    sc_disturbances.fill_scenario_data(0).to_csv(os.path.join(results_path, "sc_disturbances.csv"), index=False)
    print("finished SC disturbance test")



if __name__ == "__main__":
    main()
    