import pandas as pd
import os
import unittest
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager


class TestAfforestationTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data before running tests."""
        data_manager_path = "./data/runner_input"
        generated_scenario_afforestation_path = "./data/harvest_input"
        results_path = "./data/harvest_results"

        # Load test input data
        afforest_data = pd.read_csv(
            os.path.join(data_manager_path, "cbm_afforestation.csv"), index_col=0
        )
        config = os.path.join(data_manager_path, "cbm_factory.yaml")
        sc_data = pd.read_csv(os.path.join(data_manager_path, "scenario_dataframe.csv"))

        # Calibration and years to simulate
        calibration_year = 2020
        cls.full_rotation_scenario_years = (2100 - calibration_year) + 1
        cls.disturbances_to_track = ["DISTID1", "DISTID2"]

        # Initialize DataManager
        cls.data_manager = DataManager(
            calibration_year=calibration_year,
            config_file_path=config,
            scenario_data=sc_data,
            afforest_data=afforest_data,
        )

        # Load afforestation scenario disturbances
        cls.afforest_df = pd.read_csv(
            os.path.join(generated_scenario_afforestation_path, "afforestation_scenario_disturbances.csv")
        )

        # Create tracker instance
        cls.dist_tracker = AfforestationTracker(
            cls.data_manager, cls.disturbances_to_track, cls.afforest_df, cls.full_rotation_scenario_years
        )

        # Run the simulation
        cls.output = cls.dist_tracker.run_simulation()

        # Save outputs for inspection
        os.makedirs(results_path, exist_ok=True)
        cls.output.to_csv(os.path.join(results_path, "harvest_results.csv"))
        cls.dist_tracker.get_stands().to_csv(os.path.join(results_path, "stands_df.csv"))

    def test_output_not_empty(self):
        """Ensure that disturbances were recorded."""
        self.assertFalse(self.output.empty, "Disturbance dataframe should not be empty")

    def test_columns_exist(self):
        """Ensure required columns exist in the output."""
        expected_columns = {"Year", "Classifier1", "Classifier2", "Classifier3", "Classifier4", "Amount", "DistTypeID"}
        self.assertTrue(expected_columns.issubset(self.output.columns), "Missing expected columns in output")

    def test_mass_balance(self):
        """Ensure the total area remains consistent after disturbances."""
        initial_area = self.afforest_df["Amount"].sum()
        final_area = self.dist_tracker.get_stands()["Amount"].sum()
        self.assertAlmostEqual(initial_area, final_area, delta=1e-6, msg="Mass balance check failed!")

    def test_disturbance_types_tracked(self):
        """Ensure that disturbance types appear in the output."""
        recorded_disturbances = set(self.output["DistTypeID"].unique())
        for dist in self.disturbances_to_track:
            self.assertIn(dist, recorded_disturbances, f"Expected disturbance {dist} not found in output")

    def test_aggregated_entries(self):
        """Ensure similar stands are aggregated properly."""
        grouped_output = self.output.groupby(["Year", "Classifier1", "Classifier4"]).agg({"Amount": "sum"}).reset_index()
        self.assertTrue(len(grouped_output) <= len(self.output), "Aggregation did not reduce stand entries as expected")


if __name__ == "__main__":
    unittest.main()
