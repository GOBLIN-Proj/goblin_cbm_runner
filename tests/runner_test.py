from goblin_cbm_runner.default_runner.runner import Runner
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

    # instance of the Runner class
    runner = Runner(config, calibration_year, afforest_data, sc_data)

    # generation of data for each of the scenarios
    #runner.generate_input_data()

    # generation of aggregated results
    #runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


    sep_runs = runner.run_sep_flux_scenarios()

    for key, value in sep_runs.items():
        value.to_csv(os.path.join(results_path, key + ".csv"))


if __name__ == "__main__":
    main()
