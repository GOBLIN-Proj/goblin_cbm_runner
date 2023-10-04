from cbm_runner.runner import Runner
import pandas as pd 
import os 

def main():
    #path to data
    path = "./data"

    #afforestation data for each scenario
    afforest_data = pd.read_csv(os.path.join(path, "scenario_afforestation.csv"), index_col=0)
    
    #basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    #scenario_data 
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    #calibration and end point
    calibration_year = 2020
    forest_end_year = 2050
    
    #instance of the Runner class
    runner = Runner(config,calibration_year, forest_end_year, afforest_data, sc_data)
    
    #generation of data for each of the scenarios
    runner.generate_input_data()

    #generation of aggregated results 
    runner.run_aggregate_scenarios().to_csv(os.path.join(path, "c_aggregate.csv"))

    #generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(path, "c_flux.csv"))


if __name__ == "__main__":
    main()
    