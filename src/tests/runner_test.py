from cbm_runner.runner import Runner
import pandas as pd
import os


def main():
    path = "./data"

    afforest_data = pd.read_csv(
        os.path.join(path, "scenario_afforestation.csv"), index_col=0
    )

    config = os.path.join(path, "cbm_factory.yaml")

    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    calibration_year = 2020
    forest_end_year = 2050

    runner = Runner(config, calibration_year, forest_end_year, afforest_data, sc_data)

    #runner.generate_input_data()

    # runner.cbm_baseline_forest()["Stock"].to_csv(os.path.join(path, "baseline_forest.csv"))
    # runner.cbm_aggregate_scenario(0)["Raw"].to_csv(os.path.join(path, "scenario_raw_forest.csv"))
    # runner.afforestation_scenarios_structure().to_csv(os.path.join(path, "afforestation_structure.csv"))

    #runner.cbm_aggregate_scenario(0)["Stock"].to_csv(
        #os.path.join(path, "0_aggregate.csv")
    #)

    runner.run_flux_scenarios().to_csv(os.path.join(path, "c_flux.csv"))


if __name__ == "__main__":
    main()
