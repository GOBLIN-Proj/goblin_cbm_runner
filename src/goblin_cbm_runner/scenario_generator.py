"""
Scenario Generator
==================
Top-level orchestrator for running complete national scenarios.

Combines AF (Afforestation baseline), FM (Forest Management baseline),
and SC (Scenario) runners into a unified simulation pipeline.

Workflow:
1. Run FM baseline (2016-2070, existing forest with spinup)
2. Run AF baseline (1990-2070, historic afforestation)
3. Combine FM + AF as baseline (Scenario -1)
4. For each scenario: Run SC, combine with baseline
5. Archive all inputs and results to SQLite
6. Return combined DataFrame

Year Alignment:
Different runners have different baseline years (FM: 2016, AF: 1990, SC: 2020).
Results are merged on Year column to ensure correct alignment.

Archive Contents:
- Input tables: {runner_type}_{table_name} (e.g., AF_inventory, FM_disturbance_events)
- Results table: 'results' with runner_type column (AF, FM, SC, combined_af_fm, combined_sc_af_fm)
- Validation tables (comprehensive mode): {runner_type}_validation_{table_name}
- Reference table (comprehensive mode): _cbm_table_map

Example:
    nsg = NationalScenarioGenerator(
        scenario_data=scenario_df,
        afforestation_data=afforest_df,
        config={'afforest_delay': 5, 'annual_rate_pre_delay': 100}
    )
    results = nsg.run_flux_simulation()
    nsg.export_archive('./simulation_archive.db')
"""
from abc import ABC, abstractmethod
import os
from typing import Dict, Optional

import pandas as pd

from goblin_cbm_runner.runners.fm_runner import FMRunner
from goblin_cbm_runner.resource_manager import FMDataManager
from goblin_cbm_runner.runners.af_runner import AFRunner
from goblin_cbm_runner.resource_manager import AFDataManager
from goblin_cbm_runner.runners.sc_runner import SCRunner
from goblin_cbm_runner.resource_manager import SCDataManager
from goblin_cbm_runner.resource_manager import Paths
from goblin_cbm_runner.archive import SimulationArchive
from goblin_cbm_runner.harvest_summary import HarvestSummaryBuilder


class ScenarioGenerator(ABC):
    """
    Abstract base class for scenario generators.

    All concrete implementations must provide run_flux_simulation()
    to execute the complete simulation pipeline.
    """

    @abstractmethod
    def run_flux_simulation(self) -> pd.DataFrame:
        """
        Run the simulation for all defined scenarios.

        Returns:
            DataFrame containing combined results with 'Scenario' column.
        """
        pass


class NationalScenarioGenerator(ScenarioGenerator):
    """
    National-level scenario generator combining AF + FM + SC.

    Workflow:
    1. Run FM baseline simulation → archive inputs + results
    2. Run AF baseline simulation → archive inputs + results
    3. Combine FM + AF as baseline (Scenario -1)
    4. For each scenario:
       - Run SC simulation → archive inputs + results
       - Add results to baseline
    5. Archive combined results
    6. Return combined results

    All inputs and results are archived to SQLite for later analysis.

    Comprehensive Mode:
        When comprehensive=True, captures detailed validation tables:
        - pools (tblPoolIndicator): Carbon pools per stand per timestep
        - flux (tblFluxIndicators): Carbon fluxes per stand per timestep
        - state (tblDisturbanceIndicators): Stand state (age, disturbance type)
        - area, parameters, classifiers

        Use for validation, debugging, or NAI calculations.

    Args:
        scenario_data: DataFrame with scenario parameters (harvest rates, etc.)
        afforestation_data: DataFrame with afforestation areas per scenario
        config: Dict with 'afforest_delay' and 'annual_rate_pre_delay'
        archive_path: Optional path for SQLite archive. If None, uses temp file.
        comprehensive: If True, capture validation tables (default: False)

    Example:
        nsg = NationalScenarioGenerator(
            scenario_data=scenario_df,
            afforestation_data=afforest_df,
            config={'afforest_delay': 5, 'annual_rate_pre_delay': 100},
            archive_path='./my_simulation.db',
            comprehensive=True  # Capture validation tables
        )

        results = nsg.run_flux_simulation()
        nsg.export_archive('./final_archive.db')

        # User queries archive externally:
        # SELECT * FROM _cbm_table_map  -- See table mappings
        # SELECT * FROM AF_validation_pools WHERE scenario = -1
    """

    # Standard input files to archive
    INPUT_FILES = [
        ('inventory', 'inventory.csv'),
        ('disturbance_events', 'disturbance_events.csv'),
        ('classifiers', 'classifiers.csv'),
        ('transitions', 'transitions.csv'),
        ('growth', 'growth.csv'),
        ('age_classes', 'age_classes.csv'),
        ('disturbance_types', 'disturbance_types.csv'),
    ]

    # FM-specific files (includes spinup)
    FM_EXTRA_FILES = [
        ('standing_vol', 'standing_vol.csv'),
    ]

    def __init__(
        self,
        scenario_data: pd.DataFrame,
        afforestation_data: pd.DataFrame,
        config: Dict,
        archive_path: Optional[str] = None,
        comprehensive: bool = False,
    ):
        """
        Initialize the national scenario generator and its SQLite archive.

        See the class docstring for a full description of the parameters
        (``scenario_data``, ``afforestation_data``, ``config``,
        ``archive_path``, ``comprehensive``).
        """
        self.scenario_data = scenario_data
        self.afforestation_data = afforestation_data
        self.config = config
        self.comprehensive = comprehensive

        self.sc_data_manager = SCDataManager(
            scenario_data=scenario_data,
            afforest_data=afforestation_data,
            config=config
        )

        self.paths = Paths(sit_path=None, gen_baseline=False)

        # Initialize archive
        self.archive = SimulationArchive(path=archive_path)

        # Store run configuration
        mode = "comprehensive" if comprehensive else "lightweight"
        self.archive.store_metadata(
            config={**config, 'comprehensive': comprehensive},
            notes=f"National scenario run ({mode} mode) with {len(self.sc_data_manager.get_scenario_list())} scenarios"
        )

        # If comprehensive mode, store the table map for self-documentation
        if comprehensive:
            self.archive.store_table_map()

    def _read_input_files(self, input_dir: str, extra_files: list = None) -> Dict[str, pd.DataFrame]:
        """
        Read input CSV files from a directory.

        Args:
            input_dir: Directory containing input files
            extra_files: Additional files beyond standard INPUT_FILES

        Returns:
            Dict of {table_name: DataFrame}
        """
        files_to_read = list(self.INPUT_FILES)
        if extra_files:
            files_to_read.extend(extra_files)

        data = {}
        for table_name, filename in files_to_read:
            filepath = os.path.join(input_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath)
                    data[table_name] = df
                except Exception as e:
                    print(f"Warning: Could not read {filename}: {e}")

        return data

    def _archive_inputs(self, scenario: int, runner_type: str, input_dir: str, extra_files: list = None):
        """
        Archive input files for a runner.

        Args:
            scenario: Scenario number
            runner_type: Runner type ('AF', 'FM', 'SC')
            input_dir: Directory containing input files
            extra_files: Additional files beyond standard INPUT_FILES
        """
        data = self._read_input_files(input_dir, extra_files)
        if data:
            self.archive.store_scenario_inputs(scenario, runner_type, data)

    def _archive_harvest_summary(self, runner, runner_type: str, input_dir: str, scenario: int = None):
        """
        Retrieve harvest summary from a runner and archive it.

        Adds Expected/Diff columns by matching with disturbance_events.csv,
        then stores disturbance_summary and nai_summary tables in the archive.

        Args:
            runner: Runner instance (FMRunner, AFRunner, SCRunner) with cbm_sim attribute.
            runner_type: 'FM', 'AF', or 'SC'.
            input_dir: Directory containing disturbance_events.csv for Expected matching.
            scenario: Optional scenario number for SC runs.
        """
        harvest_summary = runner.cbm_sim._last_harvest_summary
        if harvest_summary is None:
            return

        # Load disturbance events for Expected/Diff matching
        dist_events_path = os.path.join(input_dir, 'disturbance_events.csv')
        if os.path.exists(dist_events_path):
            dist_events = pd.read_csv(dist_events_path)
            HarvestSummaryBuilder.add_expected(harvest_summary, dist_events, runner_type)

        # Archive summary tables
        self.archive.store_dataframe(
            f'{runner_type}_disturbance_summary',
            harvest_summary['disturbance_summary'],
            scenario=scenario,
        )
        self.archive.store_dataframe(
            f'{runner_type}_nai_summary',
            harvest_summary['nai_summary'],
            scenario=scenario,
        )

    def _run_fm_flux_simulation(self) -> pd.DataFrame:
        """
        Run the FM baseline simulation.

        Returns:
            DataFrame with FM flux results.
        """
        fm_runner = FMRunner(
            data_manager=FMDataManager(),
            output_path=None,
            comprehensive=self.comprehensive
        )

        # Generate input files
        fm_runner.generate_input_data()

        # Archive inputs
        self._archive_inputs(
            scenario=-1,
            runner_type='FM',
            input_dir=self.paths.get_FM_input_data_dir(),
            extra_files=self.FM_EXTRA_FILES
        )

        # Run simulation
        fm_results = fm_runner.run_flux_scenarios()

        # Archive harvest summary (always-on)
        self._archive_harvest_summary(
            fm_runner, 'FM', self.paths.get_FM_input_data_dir(), scenario=-1
        )

        # Archive results
        self.archive.store_results(
            scenario=-1,
            runner_type='FM',
            results=fm_results
        )

        # Archive validation tables if comprehensive mode
        if self.comprehensive:
            validation_tables = fm_runner.get_validation_tables()
            if validation_tables:
                self.archive.store_validation_tables(
                    scenario=-1,
                    runner_type='FM',
                    tables=validation_tables
                )

        return fm_results

    def _run_af_flux_simulation(self) -> pd.DataFrame:
        """
        Run the AF baseline simulation.

        Returns:
            DataFrame with AF flux results.
        """
        af_runner = AFRunner(
            data_manager=AFDataManager(),
            output_path=None,
            comprehensive=self.comprehensive
        )

        # Generate input files
        af_runner.generate_input_data()

        # Archive inputs
        self._archive_inputs(
            scenario=-1,
            runner_type='AF',
            input_dir=self.paths.get_AF_input_data_dir()
        )

        # Run simulation
        af_results = af_runner.run_flux_scenarios()

        # Archive harvest summary (always-on)
        self._archive_harvest_summary(
            af_runner, 'AF', self.paths.get_AF_input_data_dir(), scenario=-1
        )

        # Archive results
        self.archive.store_results(
            scenario=-1,
            runner_type='AF',
            results=af_results
        )

        # Archive validation tables if comprehensive mode
        if self.comprehensive:
            validation_tables = af_runner.get_validation_tables()
            if validation_tables:
                self.archive.store_validation_tables(
                    scenario=-1,
                    runner_type='AF',
                    tables=validation_tables
                )

        return af_results

    def _run_sc_flux_simulation(self, scenario: int) -> pd.DataFrame:
        """
        Run the SC simulation for a single scenario.

        Args:
            scenario: Scenario number (0, 1, 2, ...)

        Returns:
            DataFrame with SC flux results.
        """
        sc_runner = SCRunner(
            data_manager=self.sc_data_manager,
            scenario=scenario,
            output_path=None,
            comprehensive=self.comprehensive
        )

        # Generate input files
        sc_runner.generate_input_data()

        # Archive inputs
        self._archive_inputs(
            scenario=scenario,
            runner_type='SC',
            input_dir=self.paths.get_SC_input_data_dir()
        )

        # Run simulation
        sc_results = sc_runner.run_flux_scenarios()

        # Archive harvest summary (always-on)
        self._archive_harvest_summary(
            sc_runner, 'SC', self.paths.get_SC_input_data_dir(), scenario=scenario
        )

        # Archive results
        self.archive.store_results(
            scenario=scenario,
            runner_type='SC',
            results=sc_results
        )

        # Archive validation tables if comprehensive mode
        if self.comprehensive:
            validation_tables = sc_runner.get_validation_tables()
            if validation_tables:
                self.archive.store_validation_tables(
                    scenario=scenario,
                    runner_type='SC',
                    tables=validation_tables
                )

        return sc_results

    def _combine_results_by_year(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Combine two flux DataFrames by merging on Year column.

        Different runners have different baseline years:
        - FM: 2016-2070
        - AF: 1990-2070
        - SC: 2020-2070

        Uses explicit merge (outer join) for clarity and safety.
        NaN values from non-overlapping years are filled with 0 before summing.

        Args:
            df1: First flux DataFrame (must have 'Year' column)
            df2: Second flux DataFrame (must have 'Year' column)

        Returns:
            Combined DataFrame with summed values, sorted by Year
        """
        value_cols = [c for c in df1.columns if c not in ['Year', 'Scenario']]

        # Merge on Year (outer to include all years from both DataFrames)
        merged = pd.merge(
            df1[['Year'] + value_cols],
            df2[['Year'] + value_cols],
            on='Year',
            how='outer',
            suffixes=('_1', '_2')
        )

        # Sum corresponding columns, treating NaN as 0
        result = pd.DataFrame({'Year': merged['Year']})
        for col in value_cols:
            result[col] = merged[f'{col}_1'].fillna(0) + merged[f'{col}_2'].fillna(0)

        return result.sort_values('Year').reset_index(drop=True)

    def run_flux_simulation(self) -> pd.DataFrame:
        """
        Run the complete national simulation pipeline.

        Returns:
            DataFrame with combined results. Contains 'Scenario' column:
            - Scenario -1: FM + AF baseline
            - Scenario 0, 1, 2, ...: FM + AF + SC for each scenario
        """
        # Run baselines
        fm_results = self._run_fm_flux_simulation()
        af_results = self._run_af_flux_simulation()

        # Combine FM + AF as baseline (align by Year column)
        fm_and_af_results = self._combine_results_by_year(fm_results, af_results)

        # Archive combined baseline results
        baseline_with_scenario = fm_and_af_results.copy()
        baseline_with_scenario["Scenario"] = -1
        self.archive.store_results(
            scenario=-1,
            runner_type='combined_af_fm',
            results=baseline_with_scenario
        )

        # Get scenario list
        scenario_list = self.sc_data_manager.get_scenario_list()

        # Initialize results with baseline
        total_national_results = pd.DataFrame()
        total_national_results = pd.concat(
            [total_national_results, baseline_with_scenario],
            ignore_index=True
        )

        # Run each scenario
        for scenario in scenario_list:
            # Run SC simulation (generates, archives inputs, archives results)
            sc_results = self._run_sc_flux_simulation(scenario)

            # Combine SC with baseline (align by Year column)
            sc_af_fm_results = self._combine_results_by_year(sc_results, fm_and_af_results)
            sc_af_fm_results['Scenario'] = scenario

            # Archive combined scenario results
            self.archive.store_results(
                scenario=scenario,
                runner_type='combined_sc_af_fm',
                results=sc_af_fm_results
            )

            # Add to total results
            total_national_results = pd.concat(
                [total_national_results, sc_af_fm_results],
                ignore_index=True
            )

        return total_national_results

    def export_archive(self, destination: str):
        """
        Export the archive to a specified location.

        Args:
            destination: Path where to save the archive file

        Example:
            nsg.export_archive('./my_simulation_archive.db')
        """
        self.archive.export_to(destination)

    def get_archive(self) -> SimulationArchive:
        """
        Get the SimulationArchive instance for direct access.

        Returns:
            SimulationArchive instance

        Example:
            archive = nsg.get_archive()
            df = archive.query("SELECT * FROM inventory WHERE scenario = 0")
        """
        return self.archive

    def get_archive_path(self) -> str:
        """
        Get the path to the archive file.

        Returns:
            Path to the SQLite archive file
        """
        return self.archive.get_path()
