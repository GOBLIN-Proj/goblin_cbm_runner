from cbm_runner.default_runner import Runner
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    # path to data
    external_path = "./data/multi"
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
    runner_instances = {}

    for i in range(3):  # This will create instances from 0 to 2
        os.mkdir(os.path.join(external_path, str(i)))
        new_path = os.path.join(external_path, str(i))
        print(new_path)
        runner_instance = Runner(config, calibration_year, afforest_data, sc_data, sit_path=new_path)
        runner_instances[f'runner_{i}'] = runner_instance

    print(runner_instances)

    # generation of data for each of the scenarios
    def generate_input_data(runner):
        runner.generate_input_data()


    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(generate_input_data, runner): runner for runner in runner_instances.values()}

        for future in as_completed(futures):
            runner = futures[future]

            result = future.result()  # This will re-raise any exception caught during execution


    # generation of aggregated results
    #runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    #runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


if __name__ == "__main__":
    main()