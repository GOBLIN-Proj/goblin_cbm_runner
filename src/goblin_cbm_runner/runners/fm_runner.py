"""
FM Runner
=========
Simple, focused runner for FM (Forest Management) baseline.

Purpose:
    - Generate FM input data from database
    - Run CBM simulation with spinup
    - Return FM baseline carbon stocks and fluxes

Data Source: Database tables (FM_inventory_2100, FM_disturbances_2100, etc.)
Scenarios: None or 0 (FM baseline)
Spinup: YES (existing forest with standing volume)

Key Differences from AF:
    - Timeline: 2016-2070 (not 1990-2070)
    - Requires spinup: YES (AF doesn't need spinup)
    - Uses standing volume data for initialization

Comprehensive Mode:
    When comprehensive=True, captures validation tables (pools, flux, state, etc.)
    in addition to aggregated results. Use for validation or NAI calculations.
"""
import os
import pandas as pd
from goblin_cbm_runner.cbm.data_processing.default_processing.fm import FMDataGenerator
from goblin_cbm_runner.resource_manager import Loader
from goblin_cbm_runner.cbm.methods.cbm_methods import CBMSim
from goblin_cbm_runner.runners.base_runner import BaseRunner
from goblin_cbm_runner.resource_manager import Paths
import logging


class FMRunner(BaseRunner):
    """
    FM (Forest Management) Baseline Runner.

    Simple workflow:
    1. Generate CSV inputs from database
    2. Run CBM simulation with spinup
    3. Return results

    Unlike AF:
    - FM manages existing forest from 2016
    - FM requires spinup using standing volume data

    Comprehensive Mode:
        Set comprehensive=True to capture validation tables alongside results.
        Access via last_validation_tables after running simulation.
    """

    def __init__(self, data_manager, output_path=None, comprehensive=False):
        """
        Initialize FM runner.

        Args:
            data_manager: FMDataManager instance with FM config
            output_path: Where to save generated files (default: ./fm_output)
            comprehensive: If True, capture validation tables (pools, flux, state, etc.)
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.output_path = output_path if output_path is not None else None
        self.comprehensive = comprehensive

        self.data_manager = data_manager

        self.paths = Paths(sit_path=None, gen_baseline=False)

        # Initialize FM data generator
        self.fm_generator = FMDataGenerator(self.data_manager)

        # Initialize CBM simulation
        self.cbm_sim = CBMSim()

        # Years for simulation
        # FM baseline: 2016-2070 (existing forest) default
        self.calibration_year = data_manager.get_forest_baseline_year()
        self.forest_end_year = data_manager.get_forest_end_year()
        self.years = self.forest_end_year - self.calibration_year

        self.year_range = range(self.calibration_year, self.forest_end_year + 1)

        self.SCENARIO = -1  # FM baseline scenario (can also be None)

        # Store last validation tables (populated when comprehensive=True)
        self.last_validation_tables = None

        self.paths.make_base_data_dir()
        self.paths.make_FM_input_data_dir()

    def generate_input_data(self):
        """
        Generate FM input files from database.

        Creates in output_path:
            - inventory.csv
            - classifiers.csv
            - age_classes.csv
            - disturbance_events.csv
            - disturbance_types.csv
            - transitions.csv
            - growth.csv
            - standing_vol.csv (FM-specific: for spinup)
            - sit_config.json
            - spinup_config.json (FM-specific: spinup configuration)
        """
        self.logger.info("Generating FM input data...")

        self.paths.clean_FM_input_data_dir()

        if self.output_path is None:
            self.output_path = self.paths.get_FM_input_data_dir()
        self.logger.info(f"FM input data will be saved to: {self.output_path}")

        # Generate all SIT files (includes FM-specific standing_vol.csv and spinup_config.json)
        self.fm_generator.generate_all(self.output_path)

        self.logger.info("FM input data generated")

    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Conducts CBM simulations to calculate and aggregate carbon flux data.

        If comprehensive=True, also captures validation tables accessible via
        self.last_validation_tables after this method completes.

        Returns:
            pd.DataFrame: Aggregated carbon flux data for FM baseline.
        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        if self.comprehensive:
            # Use comprehensive simulation to capture validation tables
            result = self.cbm_sim.FM_comprehensive_simulation(
                self.SCENARIO,
                self.paths.set_FM_SIT_data_dir,
                self.paths.set_FM_spinup_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_FM_input_data_dir,
                self.paths.get_aidb_path
            )
            forest_data = result['aggregated']
            self.last_validation_tables = result['validation']
        else:
            # Use lightweight simulation (no validation tables)
            forest_data = self.cbm_sim.FM_simulate_stock(
                self.SCENARIO,
                self.paths.set_FM_SIT_data_dir,
                self.paths.set_FM_spinup_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_FM_input_data_dir,
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

    def run_validation(self):
        """
        Run CBM validation (optional, for debugging).

        Returns:
            dict: Validation dataframes from CBM simulation.
        """
        return self.cbm_sim.cbm_FM_basic_validation(
            self.years,
            self.paths.set_FM_SIT_data_dir,
            self.paths.get_FM_input_data_dir,
            self.paths.get_aidb_path
        )
