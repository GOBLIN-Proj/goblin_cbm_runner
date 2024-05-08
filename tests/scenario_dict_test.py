from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import pandas as pd
import os


def main():
    path = "./data/runner_input"

    scenario_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    print(scenario_data.columns)

    datamanager_class = DataManager(None, scenario_data)

    print(datamanager_class.scenario_disturbance_dict)

    # print(datamanager_class.gen_scenario_disturbance_dict(scenario_data))


if __name__ == "__main__":
    main()
