import pandas as pd
import os
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import unittest


class TestAfforestationTracker(unittest.TestCase):
    def test_afforestation_and_harvest(self):

        # path to data
        data_manager_path = "./data/runner_input"
        generated_scenario_afforestation_path = "./data/harvest_input"
        results_path = "./data/harvest_results"

        # afforestation data for each scenario
        afforest_data = pd.read_csv(
            os.path.join(data_manager_path, "cbm_afforestation.csv"), index_col=0
        )

        # basic configuration file
        config = os.path.join(data_manager_path, "cbm_factory.yaml")

        # scenario_data
        sc_data = pd.read_csv(os.path.join(data_manager_path, "scenario_dataframe.csv"))

        # calibration and end point
        calibration_year = 2020

        # instance of the DataManager class
        data_manager = DataManager(calibration_year = calibration_year,
                                config_file_path=config,
                                scenario_data=sc_data,
                                afforest_data=afforest_data)
        
        full_rotation_scenario_years = (2100 - calibration_year) + 1
        disturbance_dict = {
                "Sitka": {  
                    "DISTID1": 0.2,  # 20% of Sitka forests are clearfelled (DISTID1)
                    "DISTID2": 0.1   # 10% of Sitka forests are thinned (DISTID2)
                },
                "SGB": {  
                    "DISTID1": 1.0,  # 100% of SGB forests are clearfelled (DISTID1)
                    "DISTID2": 0.0   # No thinning occurs for SGB (DISTID2)
                },
                "FGB": {  
                    "DISTID1": 0.5,  # 50% of FGB forests are clearfelled (DISTID1)
                    "DISTID2": 0.3   # 30% of FGB forests are thinned (DISTID2)
                },
            }


        afforest_df = pd.read_csv(
            os.path.join(generated_scenario_afforestation_path, "afforestation_scenario_disturbances.csv")
        )

        dist_tracker = AfforestationTracker(data_manager, disturbance_dict, afforest_df, full_rotation_scenario_years)

        #print(dist_tracker.expand_disturbance_timing())

        output = dist_tracker.run_simulation()

        #save the results
        output.to_csv(os.path.join(results_path, "harvest_results.csv"))

        dist_tracker.get_stands().to_csv(os.path.join(results_path, "stands_df.csv"))

if __name__ == '__main__':
    unittest.main()

