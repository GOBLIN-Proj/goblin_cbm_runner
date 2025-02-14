from goblin_cbm_runner.geo_cbm_runner.geo_runner import GeoRunner
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
import pandas as pd
import os


def main():
    # path to data
    sit_path = "./data/geo_external"
    path = "./data/geo_cbm_input"
    results_path = "./data/geo_cbm_results"

        # Remove any files and folders that are already in sit_path
    for root, dirs, files in os.walk(sit_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


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

    # instance of the GeoDataManager class
    data_manager = GeoDataManager(calibration_year = calibration_year,
                            config_file_path=config,
                            scenario_data=sc_data,
                            afforest_data=afforest_data,
                            sit_path=sit_path)

    # instance of the Runner class
    runner = GeoRunner(data_manager)


    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


if __name__ == "__main__":
    main()
