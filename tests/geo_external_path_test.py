from goblin_cbm_runner.geo_cbm_runner.geo_runner import GeoRunner
import pandas as pd
import os


def main():
    # path to data
    sit_path = "./data/geo_external"
    path = "./data/geo_cbm_input"
    results_path = "./data/geo_cbm_results"

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

    # instance of the Runner class
    runner = GeoRunner(config, calibration_year, afforest_data, sc_data,sit_path=sit_path)


    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))

    #runner.cbm_aggregate_scenario(0)["Raw"].to_csv(os.path.join(results_path, "RAW_c_aggregate_sc0.csv"))
    #runner.cbm_aggregate_scenario(0)["Stock"].to_csv(os.path.join(results_path, "Stock_c_aggregate_sc0.csv"))

if __name__ == "__main__":
    main()
