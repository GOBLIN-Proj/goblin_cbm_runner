from goblin_cbm_runner.default_runner.runner import Runner
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import pandas as pd
import os


def main():
    # path to data
    path = "./data/runner_input"
    results_path = "./data/runner_results"

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "cbm_afforestation.csv"), index_col=0
    )

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020

    # instance of the DataManager class
    data_manager = DataManager(calibration_year = calibration_year,
                            config_file_path=config,
                            scenario_data=sc_data,
                            afforest_data=afforest_data)
    
    # instance of the Runner class
    runner = Runner(data_manager)

    # afforeation data
    runner.get_afforestation_dataframe().to_csv(os.path.join(results_path, "c_afforestation.csv"))

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


if __name__ == "__main__":
    main()
