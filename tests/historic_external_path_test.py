from goblin_cbm_runner.historic_affor.historic_affor_runner import HistoricAfforRunner
import pandas as pd
import os


def main():
    # path to data
    external_path = "./data/historic_external_path"
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
    calibration_year = 2022

    # instance of the Runner class
    runner = HistoricAfforRunner(config, calibration_year, afforest_data, sc_data, gen_validation=True, sit_path=external_path)

    # generation of data for each of the scenarios
    runner.generate_input_data()

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "historic_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "historic_c_flux.csv"))

    # generation of annual flux results libcbm 
    runner.run_libcbm_flux_scenarios().to_csv(os.path.join(results_path, "historic_c_flux_libcbm.csv"))

    # generation of annual flux results libcbm Raw
    #runner.libcbm_scenario_fluxes(-1)["Raw"].to_csv(os.path.join(results_path, "historic_c_flux_libcbm_raw.csv"))

    #generate structure data
    #runner.cbm_aggregate_scenario(-1)["Structure"].to_csv(os.path.join(results_path, "historic_structure.csv"))

    #generate raw results
    #runner.cbm_aggregate_scenario(-1)["Raw"].to_csv(os.path.join(results_path, "historic_raw.csv"))
    
    print("done")

if __name__ == "__main__":
    main()
