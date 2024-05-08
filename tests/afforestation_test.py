from cbm_runner.default_runner import Runner
#import cbm_runner.validation_data as validation_path
import pandas as pd
import os


def main():
    # path to data
    path = "./data/cbm_afforestation_input"
    results_path = "./data/cbm_afforestation_results"

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

    # instance of the Runner class
    #runner = Runner(config, calibration_year, afforest_data, sc_data, gen_validation=True, validation_path=validation_path)

    runner = Runner(config, calibration_year, afforest_data, sc_data)
    # generation of data for each of the scenarios
    runner.generate_input_data()

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


if __name__ == "__main__":
    main()
