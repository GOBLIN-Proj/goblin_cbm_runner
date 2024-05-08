from cbm_runner.geo_cbm_runner.geo_runner import GeoRunner
import pandas as pd
import os


def main():
    # path to data
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
    runner = GeoRunner(config, calibration_year, afforest_data, sc_data)

    # generation of data for each of the scenarios
    runner.generate_input_data()


if __name__ == "__main__":
    main()
