"""
SC Runner
=========
Simple, focused runner for SC (Scenario) simulations.

Purpose:
    - Generate SC input data from database templates + user DataFrames
    - Run CBM simulation for future afforestation scenarios
    - Return SC carbon stocks and fluxes

Data Source:
    - Database tables for structure (SC_* tables)
    - User-provided DataFrames for scenario areas and parameters
    - Simple config dict for delay/rate settings

Scenarios: 0, 1, 2, ... (future afforestation scenarios)
Spinup: NO (new afforestation, starts from bare land like AF)

Key Differences from AF:
    - Timeline: Configurable (default 2020-2070, not 1990-2070)
    - Uses user-provided scenario data and afforestation areas
    - Multiple scenarios supported

Comprehensive Mode:
    When comprehensive=True, captures validation tables (pools, flux, state, etc.)
    in addition to aggregated results. Use for validation or NAI calculations.
"""
import os
import pandas as pd
from goblin_cbm_runner.cbm.data_processing.default_processing.sc import SCDataGenerator
from goblin_cbm_runner.cbm.methods.cbm_methods import CBMSim
from goblin_cbm_runner.runners.base_runner import BaseRunner
from goblin_cbm_runner.resource_manager import Paths
import logging


class SCRunner(BaseRunner):
    """
    SC (Scenario) Runner.

    Simple workflow:
    1. Generate CSV inputs from database templates + user data
    2. Run CBM simulation
    3. Return results

    Unlike FM:
    - SC is new afforestation (like AF), no spinup needed
    - SC uses user-provided scenario data and afforestation areas

    Comprehensive Mode:
        Set comprehensive=True to capture validation tables alongside results.
        Access via last_validation_tables after running simulation.
    """

    def __init__(self, data_manager, scenario, output_path=None, comprehensive=False):
        """
        Initialize SC runner.

        Args:
            data_manager: SCDataManager instance with scenario data
            scenario: Scenario number (0, 1, 2, ...)
            output_path: Where to save generated files (default: ./sc_output)
            comprehensive: If True, capture validation tables (pools, flux, state, etc.)
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.output_path = output_path if output_path is not None else None
        self.comprehensive = comprehensive

        self.data_manager = data_manager
        self.scenario = scenario

        self.paths = Paths(sit_path=None, gen_baseline=False)

        # Initialize SC data generator
        self.sc_generator = SCDataGenerator(self.data_manager, scenario)

        # Initialize CBM simulation
        self.cbm_sim = CBMSim()

        # Years for simulation (SC uses forest_baseline_year, typically 2020)
        self.calibration_year = data_manager.get_forest_baseline_year()
        self.forest_end_year = data_manager.get_forest_end_year()
        self.years = self.forest_end_year - self.calibration_year

        self.year_range = range(self.calibration_year, self.forest_end_year + 1)

        # Store last validation tables (populated when comprehensive=True)
        self.last_validation_tables = None

        self.paths.make_base_data_dir()
        self.paths.make_SC_input_data_dir()

    def generate_input_data(self):
        """
        Generate SC input files from database templates + user data.

        Creates in output_path:
            - inventory.csv (from template + user areas)
            - classifiers.csv
            - age_classes.csv
            - disturbance_events.csv (DISTID4 + harvest events)
            - disturbance_types.csv
            - transitions.csv
            - growth.csv
            - sit_config.json

        NO spinup_config.json (SC doesn't need spinup)
        """
        self.logger.info(f"Generating SC input data for scenario {self.scenario}...")

        self.paths.clean_SC_input_data_dir()

        if self.output_path is None:
            self.output_path = self.paths.get_SC_input_data_dir()
        self.logger.info(f"SC input data will be saved to: {self.output_path}")

        # Generate all SIT files
        self.sc_generator.generate_all(self.output_path)

        self.logger.info(f"SC input data generated for scenario {self.scenario}")

    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Conducts CBM simulations to calculate and aggregate carbon flux data.

        If comprehensive=True, also captures validation tables accessible via
        self.last_validation_tables after this method completes.

        Returns:
            pd.DataFrame: Aggregated carbon flux data for the scenario.
        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        if self.comprehensive:
            # Use comprehensive simulation to capture validation tables
            result = self.cbm_sim.cbm_comprehensive_simulation(
                self.scenario,
                self.paths.set_SC_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_SC_input_data_dir,
                self.paths.get_aidb_path
            )
            forest_data = result['aggregated']
            self.last_validation_tables = result['validation']
        else:
            # Use lightweight simulation (no validation tables)
            forest_data = self.cbm_sim.cbm_aggregate_scenario_stock(
                self.scenario,
                self.paths.set_SC_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_SC_input_data_dir,
                self.paths.get_aidb_path
            )
            self.last_validation_tables = None

        fluxes_data = self.cbm_sim.cbm_scenario_fluxes(forest_data)

        fluxes_forest_data = pd.concat(
            [fluxes_forest_data, fluxes_data], ignore_index=True
        )

        return fluxes_forest_data

    def get_validation_tables(self):
        """
        Get validation tables from last comprehensive simulation.

        Returns:
            dict or None: Validation tables if comprehensive=True was used, else None.
                Keys: 'pools', 'flux', 'state', 'area', 'parameters', 'classifiers'
        """
        return self.last_validation_tables

    def run_aggregated_scenarios(self) -> pd.DataFrame:
        """
        Run aggregated stock simulation for the scenario.

        Returns:
            pd.DataFrame: Aggregated carbon stocks for the scenario.
        """
        forest_data = self.cbm_sim.cbm_aggregate_scenario_stock(
            self.scenario,
            self.paths.set_SC_SIT_data_dir,
            self.years,
            self.year_range,
            self.paths.get_SC_input_data_dir,
            self.paths.get_aidb_path
        )

        return forest_data

    def run_validation(self):
        """
        Runs the CBM validation for the specified years.

        Returns:
            dict: A dictionary containing the validation dataframes
        """
        data = self.cbm_sim.cbm_basic_validation(
            self.years,
            self.paths.set_SC_SIT_data_dir,
            self.paths.get_SC_input_data_dir,
            self.paths.get_aidb_path
        )
        return data

    def run_standard_flux(self):
        """
        Runs the CBM standard flux.

        Returns:
            dict: A dictionary containing flux results.
        """
        data = self.cbm_sim.run_cbm_standard_flux(
            self.years,
            self.paths.set_SC_SIT_data_dir,
            self.paths.get_SC_input_data_dir,
            self.paths.get_aidb_path
        )
        return data
