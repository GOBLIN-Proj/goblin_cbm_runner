import unittest
import os
from tempfile import TemporaryDirectory
import pandas as pd
from goblin_cbm_runner.default_runner.runner import Runner
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.geo_cbm_runner.geo_runner import GeoRunner
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager

class TestGenerateData(unittest.TestCase):

    def test_cbm_runner_creates_file(self):
        # Use a temporary directory
        with TemporaryDirectory() as tmp_dir:
        # path to data
            path = "./data/runner_input"

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

                # instance of the DataManager class
            data_manager = DataManager(calibration_year = calibration_year,
                            config_file_path=config,
                            scenario_data=sc_data,
                            afforest_data=afforest_data)

            # instance of the Runner class
            runner = Runner(data_manager)

            # path to results
            expected_file_name = "c_aggregate.csv"
            expected_file_path = os.path.join(tmp_dir, expected_file_name)

            # generation of aggregated results
            runner.run_aggregate_scenarios().to_csv(expected_file_path)

            # Check if the file was created
            self.assertTrue(os.path.exists(expected_file_path), f"File {expected_file_name} was not created in temporary directory.")

            #path to results
            expected_file_name = "c_flux.csv"
            expected_file_path = os.path.join(tmp_dir, expected_file_name)

            # generation of annual flux results
            runner.run_flux_scenarios().to_csv(expected_file_path)

            # Check if the file was created
            self.assertTrue(os.path.exists(expected_file_path), f"File {expected_file_name} was not created in temporary directory.")

    def test_geo_cbm_runner_creates_file(self):
        # Use a temporary directory
        with TemporaryDirectory() as tmp_dir:
        # path to data
            path = "./data/geo_cbm_input"

            # afforestation data for each scenario
            afforest_data = pd.read_csv(
                os.path.join(path, "geo_cbm_afforestation.csv"), index_col=0
            )

            # basic configuration file
            config = os.path.join(path, "cbm_factory.yaml")

            # scenario_data
            sc_data = pd.read_csv(os.path.join(path, "scenario_input_dataframe.csv"))

            # calibration and end point
            calibration_year = 2020

            data_manager = GeoDataManager(
                calibration_year = calibration_year, 
                config_file_path = config, 
                scenario_data = sc_data, 
                afforest_data = afforest_data
            )

            # instance of the Runner class
            runner = GeoRunner(data_manager)

            # path to results
            expected_file_name = "c_aggregate.csv"
            expected_file_path = os.path.join(tmp_dir, expected_file_name)


            # generation of aggregated results
            runner.run_aggregate_scenarios().to_csv(expected_file_path)

            # Check if the file was created
            self.assertTrue(os.path.exists(expected_file_path), f"File {expected_file_name} was not created in temporary directory.")

            #path to results
            expected_file_name = "c_flux.csv"
            expected_file_path = os.path.join(tmp_dir, expected_file_name)

            # generation of annual flux results
            runner.run_flux_scenarios().to_csv(expected_file_path)

            # Check if the file was created
            self.assertTrue(os.path.exists(expected_file_path), f"File {expected_file_name} was not created in temporary directory.")

# Running the tests
if __name__ == '__main__':
    unittest.main()