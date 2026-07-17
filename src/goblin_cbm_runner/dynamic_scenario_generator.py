"""
Dynamic Scenario Generator
===========================
Extends FM and AF timelines using NAI-based dynamic continuation,
then combines with standard SC scenarios.

Architecture:
    DynamicScenarioGenerator inherits from NationalScenarioGenerator
    for shared infrastructure (archive, paths, combining logic).

    Overrides _run_fm_flux_simulation() and _run_af_flux_simulation()
    to produce extended timelines (standard + NAI continuation).
    Overrides run_flux_simulation() to use extended baseline + SC.

    DynamicScenarioGenerator(NationalScenarioGenerator)
      overrides: run_flux_simulation(),
                 _run_fm_flux_simulation(), _run_af_flux_simulation()
      inherits:  _run_sc_flux_simulation(), _combine_results_by_year(),
                 archive infrastructure

Entry Points:
    run_flux_simulation()          — Full pipeline: extended FM + AF + SC
    run_baseline_flux_simulation() — Extended FM + AF baseline only (no SC)

Usage:
    from goblin_cbm_runner.dynamic_scenario_generator import DynamicScenarioGenerator

    # Use all defaults from DF_config.yaml:
    dsg = DynamicScenarioGenerator(
        scenario_data=scenario_df,
        afforestation_data=afforest_df,
        config={'afforest_delay': 5, 'annual_rate_pre_delay': 100},
    )

    # Or override specific parameters:
    dsg = DynamicScenarioGenerator(
        scenario_data=scenario_df,
        afforestation_data=afforest_df,
        config={'afforest_delay': 5, 'annual_rate_pre_delay': 100},
        dynamic_config={
            'harvest_ratio': 0.85,
            'dynamic_years': 50,
        }
    )

    results = dsg.run_flux_simulation()       # pd.DataFrame — extended FM + AF + SC
    fm_dynamic = dsg.get_fm_dynamic_result()   # DynamicSimulationResult (diagnostics)
    af_dynamic = dsg.get_af_dynamic_result()   # DynamicSimulationResult (diagnostics)
    dsg.export_archive('./simulation_archive.db')
"""
from typing import Dict, Optional

import pandas as pd

from goblin_cbm_runner.scenario_generator import NationalScenarioGenerator
from goblin_cbm_runner.runners.dynamic_fm_runner import DynamicFMRunner
from goblin_cbm_runner.runners.dynamic_af_runner import DynamicAFRunner
from goblin_cbm_runner.resource_manager import FMDataManager, AFDataManager, DFDataManager, Loader
from goblin_cbm_runner.nai.dynamic_runner import DynamicRunner, DynamicSimulationResult


class DynamicScenarioGenerator(NationalScenarioGenerator):
    """
    Scenario generator with NAI-based dynamic continuation for FM and AF.

    Extends FM and AF baselines beyond the standard pipeline's end year
    using NAI-driven harvest, then combines with standard SC scenarios.

    Inherits from NationalScenarioGenerator for shared infrastructure
    (archive, paths, year-alignment combining, SC runner).

    Entry points:
        run_flux_simulation() — Full pipeline: extended FM + AF + SC
        run_baseline_flux_simulation() — Extended FM + AF baseline only

    Args:
        scenario_data: DataFrame with scenario parameters
        afforestation_data: DataFrame with afforestation areas per scenario
        config: Dict with 'afforest_delay' and 'annual_rate_pre_delay'
        dynamic_config: Dict with DynamicRunner overrides. Any keys provided
            override the defaults from DF_config.yaml. Common keys:
            - harvest_ratio: Target proportion of NAI to harvest (default: 0.75)
            - clearfell_thinning_split: Dict mapping disturbance type to proportion
            - dynamic_years: Years to simulate beyond end year (default: 30)
            - scheduled_disturbances: List of dicts for fire/wind events
            If None, all defaults from DF_config.yaml are used.
        archive_path: Optional path for SQLite archive
        comprehensive: If True, capture validation tables
    """

    def __init__(
        self,
        scenario_data: pd.DataFrame,
        afforestation_data: pd.DataFrame,
        config: Dict,
        dynamic_config: Optional[Dict] = None,
        archive_path: Optional[str] = None,
        comprehensive: bool = False,
    ):
        """
        Initialize the dynamic scenario generator.

        Builds the DFDataManager (DF_config.yaml defaults merged with
        ``dynamic_config`` overrides) and initializes the inherited NSG pipeline.
        See the class docstring for a full description of the parameters.
        """
        # Dynamic configuration: YAML defaults merged with user overrides
        self.df_data_manager = DFDataManager(config=dynamic_config)

        # Initialize the full NSG pipeline (archive, paths, sc_data_manager, etc.)
        super().__init__(
            scenario_data=scenario_data,
            afforestation_data=afforestation_data,
            config=config,
            archive_path=archive_path,
            comprehensive=comprehensive,
        )

        # Extend SC end year to match dynamic timeline
        sc_base_end_year = self.sc_data_manager.get_forest_end_year()
        extended_end_year = sc_base_end_year + self.df_data_manager.get_dynamic_years()
        self.sc_data_manager.cbm_default_config["simulation"]["end_year"] = extended_end_year

        # Dynamic continuation results (populated during _run_fm/af_flux_simulation)
        self._fm_dynamic_result = None
        self._af_dynamic_result = None


    def run_flux_simulation(self) -> pd.DataFrame:
        """
        Run the complete dynamic simulation pipeline.

        1. Run extended FM + AF baseline (standard + NAI continuation)
        2. For each scenario: run standard SC, combine with extended baseline
        3. Archive all results

        Returns:
            pd.DataFrame: Combined results with 'Scenario' column:
                - Scenario -1: Extended FM + AF baseline
                - Scenario 0, 1, 2, ...: Extended FM + AF + SC for each scenario
        """
        baseline_cache = self.run_baseline_flux_simulation()

        # Initialize results with baseline
        total_national_results = pd.concat(
            [pd.DataFrame(), baseline_cache],
            ignore_index=True
        )

        # Get scenario list
        scenario_list = self.sc_data_manager.get_scenario_list()

        # Run each scenario
        for scenario in scenario_list:
            sc_results = self._run_sc_flux_simulation(scenario)

            # Combine SC with extended baseline (align by Year column)
            sc_af_fm_results = self._combine_results_by_year(sc_results, baseline_cache.copy())
            sc_af_fm_results['Scenario'] = scenario

            self.archive.store_results(
                scenario=scenario,
                runner_type='combined_sc_af_fm',
                results=sc_af_fm_results
            )

            total_national_results = pd.concat(
                [total_national_results, sc_af_fm_results],
                ignore_index=True
            )

        return total_national_results

    # ------------------------------------------------------------------
    # Baseline: extended FM + AF (no SC)
    # ------------------------------------------------------------------

    def run_baseline_flux_simulation(self) -> pd.DataFrame:
        """
        Run extended FM and AF simulations, return combined baseline.

        FM + AF only, no SC.
        1. Run FM standard + NAI continuation → extended FM flux
        2. Run AF standard + NAI continuation → extended AF flux
        3. Combine FM + AF by year → extended baseline (Scenario -1)

        Returns:
            pd.DataFrame: Combined FM + AF baseline with extended timeline.
                - Scenario -1 only
                - Year range covers standard + dynamic continuation period
        """
        # Run extended FM and AF
        fm_extended = self._run_fm_flux_simulation()
        af_extended = self._run_af_flux_simulation()

        # Combine FM + AF as baseline (align by Year column)
        baseline = self._combine_results_by_year(fm_extended, af_extended)
        baseline['Scenario'] = -1

        # Archive combined baseline
        self.archive.store_results(
            scenario=-1,
            runner_type='combined_af_fm',
            results=baseline
        )

        return baseline

    # ------------------------------------------------------------------
    # Override NSG runner methods to produce extended timelines
    # ------------------------------------------------------------------

    def _run_fm_flux_simulation(self) -> pd.DataFrame:
        """
        Run FM baseline + NAI dynamic continuation, returning extended flux.

        1. Run DynamicFMRunner (standard FM simulation with state capture)
        2. Run DynamicRunner continuation from captured final state
        3. Convert dynamic stock to flux
        4. Return stitched flux covering standard + dynamic period

        Archives:
        - FM inputs
        - FM extended flux (complete timeline)
        - FM validation tables (if comprehensive)
        - Dynamic FM diagnostic data (NAI history, sustainability metrics)

        Returns:
            DataFrame with FM flux results covering the extended timeline.
        """
        # --- Standard FM simulation (with state capture) ---
        fm_runner = DynamicFMRunner(
            data_manager=FMDataManager(),
            output_path=None,
            comprehensive=self.comprehensive
        )

        fm_runner.generate_input_data()

        self._archive_inputs(
            scenario=-1,
            runner_type='FM',
            input_dir=self.paths.get_FM_input_data_dir(),
            extra_files=self.FM_EXTRA_FILES
        )

        fm_flux = fm_runner.run_flux_scenarios()

        # Archive harvest summary (always-on)
        self._archive_harvest_summary(
            fm_runner, 'FM', self.paths.get_FM_input_data_dir(), scenario=-1
        )

        if self.comprehensive:
            validation_tables = fm_runner.get_validation_tables()
            if validation_tables:
                self.archive.store_validation_tables(
                    scenario=-1,
                    runner_type='FM',
                    tables=validation_tables
                )

        # --- Dynamic NAI continuation ---
        self._fm_dynamic_result = self._run_dynamic_continuation(
            runner=fm_runner, runner_label='FM'
        )

        # --- Stitch: convert dynamic stock to flux and extend ---
        if self._fm_dynamic_result is not None:
            dynamic_flux = self._stock_to_flux(
                self._fm_dynamic_result.aggregated, scenario=-1
            )
            fm_flux = pd.concat([fm_flux, dynamic_flux], ignore_index=True)

        # Archive the complete extended FM flux
        self.archive.store_results(
            scenario=-1,
            runner_type='FM',
            results=fm_flux
        )

        return fm_flux

    def _run_af_flux_simulation(self) -> pd.DataFrame:
        """
        Run AF baseline + NAI dynamic continuation, returning extended flux.

        1. Run DynamicAFRunner (standard AF simulation with state capture)
        2. Run DynamicRunner continuation from captured final state
        3. Convert dynamic stock to flux
        4. Return stitched flux covering standard + dynamic period

        Archives:
        - AF inputs
        - AF extended flux (complete timeline)
        - AF validation tables (if comprehensive)
        - Dynamic AF diagnostic data (NAI history, sustainability metrics)

        Returns:
            DataFrame with AF flux results covering the extended timeline.
        """
        # --- Standard AF simulation (with state capture) ---
        af_runner = DynamicAFRunner(
            data_manager=AFDataManager(),
            output_path=None,
            comprehensive=self.comprehensive
        )

        af_runner.generate_input_data()

        self._archive_inputs(
            scenario=-1,
            runner_type='AF',
            input_dir=self.paths.get_AF_input_data_dir()
        )

        af_flux = af_runner.run_flux_scenarios()

        # Archive harvest summary (always-on)
        self._archive_harvest_summary(
            af_runner, 'AF', self.paths.get_AF_input_data_dir(), scenario=-1
        )

        if self.comprehensive:
            validation_tables = af_runner.get_validation_tables()
            if validation_tables:
                self.archive.store_validation_tables(
                    scenario=-1,
                    runner_type='AF',
                    tables=validation_tables
                )

        # --- Dynamic NAI continuation ---
        self._af_dynamic_result = self._run_dynamic_continuation(
            runner=af_runner, runner_label='AF'
        )

        # --- Stitch: convert dynamic stock to flux and extend ---
        if self._af_dynamic_result is not None:
            dynamic_flux = self._stock_to_flux(
                self._af_dynamic_result.aggregated, scenario=-1
            )
            af_flux = pd.concat([af_flux, dynamic_flux], ignore_index=True)

        # Archive the complete extended AF flux
        self.archive.store_results(
            scenario=-1,
            runner_type='AF',
            results=af_flux
        )

        return af_flux

    # ------------------------------------------------------------------
    # Dynamic continuation
    # ------------------------------------------------------------------

    def _run_dynamic_continuation(
        self,
        runner,
        runner_label: str,
    ) -> Optional[DynamicSimulationResult]:
        """
        Run NAI-based dynamic continuation from a runner's final state.

        Archives diagnostic data (NAI history, sustainability metrics,
        validation tables) but NOT the raw stock data to the results table.

        Args:
            runner: DynamicFMRunner or DynamicAFRunner that has completed simulation.
            runner_label: 'FM' or 'AF' (for archive keys and logging).

        Returns:
            DynamicSimulationResult or None if state is unavailable.
        """
        cbm_vars = runner.get_final_cbm_vars()
        sit = runner.get_sit()

        if cbm_vars is None or sit is None:
            print(f"Warning: {runner_label} final state not available, skipping dynamic continuation")
            return None

        base_year = runner.data_manager.get_forest_end_year()

        # Extract last-year per-species harvest from the standard pipeline's
        # final cbm_vars.flux (tC/ha density units). This is passed to
        # run_from_state() so that t=1 has realistic harvest instead of zero
        # harvest (which causes a flux spike at the transition year).
        #
        # Using cbm_vars.flux (tC/ha) is critical: the scheduler works in
        # tC/ha units (from cbm_vars.pools), so initial_species_nai must
        # also be in tC/ha. The archive HarvestC (total tC from CBMOutput)
        # is 10-30x larger due to area multiplication, causing over-targeting.
        initial_species_nai = None
        try:
            flux_df = cbm_vars.flux.to_pandas()
            classifiers_df = cbm_vars.classifiers.to_pandas()
            species_col = self.df_data_manager.get_species_column()

            # Per-stand harvest density (tC/ha)
            harvest_flux = pd.Series(0.0, index=range(len(flux_df)))
            for col in ['DisturbanceSoftProduction', 'DisturbanceHardProduction',
                        'DisturbanceDOMProduction']:
                if col in flux_df.columns:
                    harvest_flux += flux_df[col].values

            if species_col in classifiers_df.columns and harvest_flux.sum() > 0:
                harvest_ratio = self.df_data_manager.get_harvest_ratio()
                species_ids = classifiers_df[species_col].values
                initial_species_nai = {}
                for sp_id in pd.unique(species_ids):
                    mask = species_ids == sp_id
                    sp_harvest = float(harvest_flux[mask].sum())
                    if sp_harvest > 0:
                        initial_species_nai[sp_id] = sp_harvest / harvest_ratio
            else:
                print(f"Warning ({runner_label}): No harvest flux in final cbm_vars — skipping first-step seeding")
        except Exception as e:
            print(f"Warning ({runner_label}): Could not extract harvest flux for seeding: {e}")

        # Build DynamicRunner from data manager (YAML defaults + user overrides)
        loader = Loader()
        disturbance_timing = loader.disturbance_time()

        dynamic_runner = DynamicRunner(
            harvest_ratio=self.df_data_manager.get_harvest_ratio(),
            clearfell_thinning_split=self.df_data_manager.get_clearfell_thinning_split(),
            disturbance_timing=disturbance_timing,
            scheduled_disturbances=self.df_data_manager.get_scheduled_disturbances(),
            species_column=self.df_data_manager.get_species_column()
        )

        result = dynamic_runner.run_from_state(
            initial_cbm_vars=cbm_vars,
            sit=sit,
            years=self.df_data_manager.get_dynamic_years(),
            base_year=base_year,
            capture_validation_tables=self.comprehensive,
            cbm_vars_dump_dir=self.df_data_manager.get_cbm_vars_dump_dir(),
            initial_species_nai=initial_species_nai
        )

        # Archive diagnostic data only (not raw stock to results table)
        archive_prefix = runner_label.lower()
        runner_type = f'dynamic_{runner_label}'

        if not result.nai_history.empty:
            self.archive.store_dataframe(
                f'{archive_prefix}_dynamic_nai_history',
                result.nai_history
            )

        if not result.sustainability_metrics.empty:
            self.archive.store_dataframe(
                f'{archive_prefix}_dynamic_sustainability_metrics',
                result.sustainability_metrics
            )

        # Archive harvest summary (always-on, matches standard pipeline format)
        if result.harvest_summary:
            if 'disturbance_summary' in result.harvest_summary:
                self.archive.store_dataframe(
                    f'{runner_type}_disturbance_summary',
                    result.harvest_summary['disturbance_summary'],
                    scenario=-1,
                )
            if 'nai_summary' in result.harvest_summary:
                self.archive.store_dataframe(
                    f'{runner_type}_nai_summary',
                    result.harvest_summary['nai_summary'],
                    scenario=-1,
                )

        if self.comprehensive and result.validation_tables:
            self.archive.store_validation_tables(
                scenario=-1,
                runner_type=runner_type,
                tables=result.validation_tables
            )

        return result

    # ------------------------------------------------------------------
    # Stock-to-flux conversion
    # ------------------------------------------------------------------

    def _stock_to_flux(self, stock_df: pd.DataFrame, scenario: int) -> pd.DataFrame:
        """
        Convert stock data to flux (year-over-year differences).

        Mirrors the logic of CBMSim.cbm_scenario_fluxes() for dynamic
        aggregated data: flux[Year Y] = stock[Y] - stock[Y-1], labeled with
        the later (upper) row's year. The first stock row (t=0, the state
        inherited from the standard simulation) serves only as the baseline
        for differencing and is not itself emitted as a flux row, so the
        resulting flux DataFrame has one fewer row than the stock.

        For dynamic continuation from 2070 with 30 years:
        - Stock years: [2070, 2071, ..., 2100] — 31 rows
        - Flux years:  [2071, 2072, ..., 2100] — 30 rows
        - Standard FM flux ends at 2070 (a real, non-zero value), so these
          connect seamlessly with no duplicate or missing year at the seam.

        Args:
            stock_df: DataFrame with Year, AGB, BGB, Deadwood, Litter,
                      Soil, Harvest, Total Ecosystem
            scenario: Scenario number to assign

        Returns:
            DataFrame with flux values, Year, and Scenario columns.
        """
        value_cols = ['AGB', 'BGB', 'Deadwood', 'Litter', 'Soil', 'Harvest', 'Total Ecosystem']
        stock = stock_df.reset_index(drop=True)

        fluxes = []
        for i in range(1, len(stock)):
            row = {'Year': int(stock.loc[i, 'Year']), 'Scenario': scenario}
            for col in value_cols:
                row[col] = stock.loc[i, col] - stock.loc[i - 1, col]
            fluxes.append(row)

        return pd.DataFrame(fluxes)

    # ------------------------------------------------------------------
    # Accessors for dynamic diagnostic results
    # ------------------------------------------------------------------

    def get_fm_dynamic_result(self) -> Optional[DynamicSimulationResult]:
        """
        Get the FM DynamicSimulationResult from the last run.

        Contains NAI history, harvest history, sustainability metrics,
        and optionally validation tables. For diagnostic use.

        Returns:
            DynamicSimulationResult or None if not yet run.
        """
        return self._fm_dynamic_result

    def get_af_dynamic_result(self) -> Optional[DynamicSimulationResult]:
        """
        Get the AF DynamicSimulationResult from the last run.

        Contains NAI history, harvest history, sustainability metrics,
        and optionally validation tables. For diagnostic use.

        Returns:
            DynamicSimulationResult or None if not yet run.
        """
        return self._af_dynamic_result
