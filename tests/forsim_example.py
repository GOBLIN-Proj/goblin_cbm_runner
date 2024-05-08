from goblin_cbm_runner.forest_sim.forestsim_runner import ForestSimRunner
import pandas as pd
import os


def main():
    # path to data
    path = "./data/forsim_input"
    results_path = "./data/forsim_results"

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "scenario_afforestation_calculated.csv"), index_col=0
    )

    afforest_data_annual = pd.read_csv(
        os.path.join(path, "scenario_afforestation_annual.csv"), index_col=0
    )

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_input_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020

    # instance of the Runner class
    runner = ForestSimRunner(config, calibration_year, afforest_data, afforest_data_annual, sc_data)

    # generation of data for each of the scenarios
    runner.generate_input_data()

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "forsim_c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "forsim_c_flux.csv"))


if __name__ == "__main__":
    main()
