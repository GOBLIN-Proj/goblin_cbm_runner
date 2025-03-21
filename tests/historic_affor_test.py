from goblin_cbm_runner.historic_affor.historic_affor_runner import HistoricAfforRunner
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import pandas as pd
import os


def main():
    # path to data
    path = "./data/historic_affor_input"
    results_path = "./data/historic_affor_results"

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

    data_manager = DataManager(
        calibration_year=calibration_year,
        config_file_path=config,
        afforest_data=afforest_data,
        scenario_data=sc_data)
    
    # instance of the Runner class
    runner = HistoricAfforRunner(data_manager)

    # generation of data for each of the scenarios
    runner.generate_input_data()

    # generation of aggregated results
    #runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "historic_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "historic_c_flux.csv"))

    # generation of annual flux results libcbm 
    #runner.run_libcbm_flux_scenarios().to_csv(os.path.join(results_path, "historic_c_flux_libcbm.csv"))

    # generate raw scenario flux

    # run base flux 
    runner.run_baseline_summary_flux().to_csv(os.path.join(results_path, "historic_c_flux_summary_baseline_managed.csv"))

    # run base flux libcbm
    #runner.run_baseline_raw().to_csv(os.path.join(results_path, "historic_c_stock_raw_baseline.csv"))
    
    print("done")

if __name__ == "__main__":
    main()
