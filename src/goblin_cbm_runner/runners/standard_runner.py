"""
Standard Runner
=================
Accepts user-provided CSV files for CBM simulation without the internal database.

Purpose:
    - Load SIT input data from a user-specified directory
    - Run CBM simulation (no spinup, static disturbance schedule)
    - Return carbon flux DataFrame in the standard format

Mode: Static
    User provides disturbance_events.csv with an explicit harvest schedule.
    The ireland_cbm_defaults_v6.1.db AIDB is still required (bundled with package).

Required files in csv_directory:
    - inventory.csv
    - classifiers.csv
    - age_classes.csv
    - disturbance_types.csv
    - disturbance_events.csv
    - transitions.csv
    - growth.csv
    - sit_config.json

Example:
    runner = StandardRunner(
        csv_directory='./my_stands/',
        config={'baseline_year': 2020, 'end_year': 2050},
    )
    runner.generate_input_data()
    results = runner.run_flux_scenarios()

Template CSVs:
    src/goblin_cbm_runner/data/STANDARD_template/
    Copy and edit for your forest; see README.md there for column docs.

Note:
    NAI-based mode (no disturbance_events.csv needed) is planned for Phase 4b.
    See refactor/developer_guide/06_STANDALONE_RUNNER.md for design.
"""
import os
import pandas as pd

from libcbm.input.sit import sit_cbm_factory

from goblin_cbm_runner.cbm.methods.cbm_methods import CBMSim
from goblin_cbm_runner.runners.base_runner import BaseRunner
from goblin_cbm_runner.resource_manager import Paths
import logging


REQUIRED_FILES = [
    "inventory.csv",
    "classifiers.csv",
    "age_classes.csv",
    "disturbance_types.csv",
    "disturbance_events.csv",
    "transitions.csv",
    "growth.csv",
    "sit_config.json",
]


class StandardRunner(BaseRunner):
    """
    Runner that accepts user-provided CSV files, bypassing the internal database.

    Static mode: user provides disturbance_events.csv with explicit harvest schedule.
    No spinup is performed (suitable for new afforestation or age-based stands).

    The ireland_cbm_defaults_v6.1.db AIDB is still required — it is bundled with the
    package and loaded automatically.
    """

    def __init__(self, csv_directory: str, config: dict = None, scenario: int = 0):
        """
        Initialize Standard runner.

        Args:
            csv_directory: Path to directory containing required SIT CSV files.
            config: Optional overrides. Keys:
                - 'baseline_year' (int): Start year for output (default 2020)
                - 'end_year' (int): End year for simulation (default 2050)
            scenario: Scenario number for output labelling (default 0).
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.csv_directory = os.path.abspath(csv_directory)
        self.config = config or {}
        self.scenario = scenario

        self.paths = Paths(sit_path=None, gen_baseline=False)
        self.cbm_sim = CBMSim()

        self.calibration_year = self.config.get("baseline_year", 2020)
        self.forest_end_year = self.config.get("end_year", 2050)
        self.years = self.forest_end_year - self.calibration_year
        self.year_range = range(self.calibration_year, self.forest_end_year + 1)

    def generate_input_data(self) -> None:
        """
        Validate that all required SIT files are present in csv_directory.

        Raises:
            FileNotFoundError: If any required file is missing.
        """
        missing = [
            f for f in REQUIRED_FILES
            if not os.path.exists(os.path.join(self.csv_directory, f))
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing required files in {self.csv_directory}: {missing}\n"
                f"See src/goblin_cbm_runner/data/STANDARD_template/ for examples."
            )
        self.logger.info(f"All required files found in: {self.csv_directory}")

    def _get_input_dir(self) -> str:
        """Callable returning user's CSV directory (matches Paths interface)."""
        return self.csv_directory

    def _load_sit(self, path: str, db_path: str):
        """
        Load SIT from user's CSV directory.

        Callable with signature (path, db_path) -> (sit, classifiers, inventory),
        matching the interface expected by CBMSim simulation methods.

        Args:
            path: Input directory (will be self.csv_directory).
            db_path: Path to AIDB database.

        Returns:
            tuple: (sit, classifiers, inventory)
        """
        sit_config_path = os.path.join(path, "sit_config.json")
        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)
        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
        return sit, classifiers, inventory

    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Run CBM simulation from user-provided CSV files and return flux results.

        Uses the static disturbance schedule from disturbance_events.csv.
        No spinup is performed.

        Returns:
            pd.DataFrame: Carbon flux data with Year column and ecosystem carbon pools.
        """
        self.logger.info(
            f"Starting Standard simulation (scenario {self.scenario}, "
            f"{self.calibration_year}–{self.forest_end_year})..."
        )

        forest_data = self.cbm_sim.cbm_aggregate_scenario_stock(
            self.scenario,
            self._load_sit,
            self.years,
            self.year_range,
            self._get_input_dir,
            self.paths.get_aidb_path,
        )

        return self.cbm_sim.cbm_scenario_fluxes(forest_data)
