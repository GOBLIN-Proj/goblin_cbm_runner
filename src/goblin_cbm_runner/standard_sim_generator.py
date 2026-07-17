"""
Standard Simulation Generator
==============================
Entry-point for StandardRunner simulations with archive output and template retrieval.

Wraps StandardRunner with:
- Archive output (SimulationArchive → SQLite)
- Template retrieval (get_template classmethod)
- Consistent run_flux_simulation() / export_archive() interface

This mirrors how NationalScenarioGenerator wraps FM/AF/SC runners, but for
user-provided CSV files with no internal database dependency.

Usage:
    # 1. Copy template CSVs to your directory (first time only)
    StandardSimGenerator.get_template('./my_forest/')

    # 2. Edit the CSVs in ./my_forest/ for your forest stands

    # 3. Run simulation
    gen = StandardSimGenerator(
        csv_directory='./my_forest/',
        config={'baseline_year': 2020, 'end_year': 2050},
    )
    results = gen.run_flux_simulation()
    gen.export_archive('./my_run.db')

For NAI-based dynamic continuation, see DynamicStandardSimGenerator.
"""
import shutil
from pathlib import Path
from typing import Optional

import pandas as pd

from goblin_cbm_runner.scenario_generator import ScenarioGenerator
from goblin_cbm_runner.runners.standard_runner import StandardRunner
from goblin_cbm_runner.archive import SimulationArchive


class StandardSimGenerator(ScenarioGenerator):
    """
    Entry-point for StandardRunner simulations.

    Wraps StandardRunner with archive output and template retrieval.

    Args:
        csv_directory: Path to user's SIT CSV files.
        config: {'baseline_year': int, 'end_year': int}
        scenario: Scenario label for archive (default 0).
        archive_path: Optional SQLite output path.
    """

    def __init__(
        self,
        csv_directory: str,
        config: Optional[dict] = None,
        scenario: int = 0,
        archive_path: Optional[str] = None,
    ):
        """
        Initialize the standard-simulation generator and its SQLite archive.

        See the class docstring for a description of the parameters
        (``csv_directory``, ``config``, ``scenario``, ``archive_path``).
        """
        self.csv_directory = csv_directory
        self.config = config or {}
        self.scenario = scenario
        self.archive = SimulationArchive(path=archive_path)

    @classmethod
    def get_template(cls, output_dir: str) -> None:
        """
        Copy the STANDARD_template files to output_dir.

        Creates output_dir if it doesn't exist. Copies the bundled template
        CSVs (inventory, classifiers, growth, etc.) so the user can edit them
        for their own forest.

        Args:
            output_dir: Destination directory path.
        """
        template_dir = Path(__file__).parent / 'data' / 'STANDARD_template'
        shutil.copytree(str(template_dir), output_dir, dirs_exist_ok=True)
        print(f"Template copied to: {output_dir}")

    def run_flux_simulation(self) -> pd.DataFrame:
        """
        Run static CBM simulation from user-provided CSV files.

        Runs StandardRunner with the configured CSV directory, archives
        inputs and results, and returns the flux DataFrame.

        Returns:
            pd.DataFrame: Carbon flux data with Year and Scenario columns.
        """
        runner = StandardRunner(
            csv_directory=self.csv_directory,
            config=self.config,
            scenario=self.scenario,
        )
        runner.generate_input_data()
        results = runner.run_flux_scenarios()
        results['Scenario'] = self.scenario

        self.archive.store_results(
            scenario=self.scenario,
            runner_type='standard',
            results=results,
        )
        return results

    def export_archive(self, destination: str) -> None:
        """
        Export the archive to a specified path.

        Args:
            destination: Path where to save the SQLite archive file.
        """
        self.archive.export_to(destination)

    def get_archive(self) -> SimulationArchive:
        """Return the SimulationArchive instance for direct access."""
        return self.archive
