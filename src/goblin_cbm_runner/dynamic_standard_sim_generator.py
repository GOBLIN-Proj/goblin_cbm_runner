"""
Dynamic Standard Simulation Generator
=======================================
Entry-point for NAI-based simulation from user-provided inventory.

Runs DynamicStandardRunner (spinup + optional static phase), then continues
with DynamicRunner (NAI-based harvest) for dynamic_years. No internal database
required for inventory or growth curves — everything comes from user CSVs.

The ireland_cbm_defaults_v6.1.db AIDB is still required (bundled with the package).

Design:
    DynamicStandardSimGenerator(StandardSimGenerator)
      overrides: run_flux_simulation()
      adds:      _run_dynamic_continuation(), _extract_initial_species_nai(),
                 _stock_to_flux(), get_dynamic_result()

NAI from day 1 (default):
    When end_year = baseline_year (years=0), only spinup fires.
    _last_cbm_vars = initial pool state. DynamicRunner starts from there.
    No pre-computed disturbance schedule required.
    No transition spike (nothing to transition from).

Optional static warm-up:
    Set end_year > baseline_year. Static disturbance schedule runs first;
    DynamicRunner continues after end_year.
    disturbance_events.csv must contain a valid schedule.

Usage:
    # 1. Copy template
    DynamicStandardSimGenerator.get_template('./my_forest/')

    # 2. Edit CSVs (disturbance_events.csv may be empty for pure NAI)

    # 3. Run
    gen = DynamicStandardSimGenerator(
        csv_directory='./my_forest/',
        config={'baseline_year': 2020},        # end_year omitted → years=0
        dynamic_config={'harvest_ratio': 0.75, 'dynamic_years': 50},
    )
    results = gen.run_flux_simulation()
    gen.export_archive('./my_run.db')

    # Diagnostics
    dr = gen.get_dynamic_result()
    print(dr.nai_history)
    print(dr.sustainability_metrics)
"""
from typing import Optional

import pandas as pd

from goblin_cbm_runner.standard_sim_generator import StandardSimGenerator
from goblin_cbm_runner.runners.dynamic_standard_runner import DynamicStandardRunner
from goblin_cbm_runner.resource_manager import DFDataManager, Loader
from goblin_cbm_runner.nai.dynamic_runner import DynamicRunner, DynamicSimulationResult


class DynamicStandardSimGenerator(StandardSimGenerator):
    """
    Entry-point for NAI-based simulation from user-provided inventory.

    Extends StandardSimGenerator with DynamicRunner continuation.

    Args:
        csv_directory: Path to user's SIT CSV files.
        config: {'baseline_year': int, 'end_year': int}
            For pure NAI: omit end_year (defaults to baseline_year, years=0).
        dynamic_config: Override DF_config.yaml defaults. Common keys:
            - harvest_ratio (default 0.75)
            - dynamic_years (default 30)
            - clearfell_thinning_split
        scenario: Scenario label (default 0).
        archive_path: Optional SQLite output path.
    """

    def __init__(
        self,
        csv_directory: str,
        config: Optional[dict] = None,
        dynamic_config: Optional[dict] = None,
        scenario: int = 0,
        archive_path: Optional[str] = None,
    ):
        """
        Initialize the dynamic standard-simulation generator.

        Builds the DFDataManager (DF_config.yaml defaults merged with
        ``dynamic_config`` overrides) and initializes the inherited
        StandardSimGenerator. See the class docstring for a full description of
        the parameters.
        """
        self.df_data_manager = DFDataManager(config=dynamic_config)
        super().__init__(
            csv_directory=csv_directory,
            config=config,
            scenario=scenario,
            archive_path=archive_path,
        )
        self._dynamic_result: Optional[DynamicSimulationResult] = None

    def run_flux_simulation(self) -> pd.DataFrame:
        """
        Run dynamic CBM simulation: spinup (+ optional static phase) then NAI.

        1. DynamicStandardRunner: spinup + static phase (empty if years=0)
        2. DynamicRunner: NAI-based continuation from final state
        3. Stitch static + dynamic flux into one DataFrame
        4. Archive results and diagnostics

        Returns:
            pd.DataFrame: Carbon flux data spanning the full timeline.
        """
        runner = DynamicStandardRunner(
            csv_directory=self.csv_directory,
            config=self.config,
            scenario=self.scenario,
        )
        runner.generate_input_data()
        static_flux = runner.run_flux_scenarios()

        self._dynamic_result = self._run_dynamic_continuation(runner)

        if self._dynamic_result is not None:
            dynamic_flux = self._stock_to_flux(
                self._dynamic_result.aggregated, self.scenario
            )
            if static_flux.empty:
                full_flux = dynamic_flux
            else:
                full_flux = pd.concat([static_flux, dynamic_flux], ignore_index=True)
        else:
            full_flux = static_flux

        full_flux['Scenario'] = self.scenario

        self.archive.store_results(
            scenario=self.scenario,
            runner_type='dynamic_standard',
            results=full_flux,
        )
        return full_flux

    def _run_dynamic_continuation(
        self, runner: DynamicStandardRunner
    ) -> Optional[DynamicSimulationResult]:
        """
        Run NAI continuation from runner's final state.

        Extracts _last_cbm_vars and _last_sit from the runner, builds a
        DynamicRunner, and runs for dynamic_years. When years=0 (pure NAI),
        initial_species_nai is None — DynamicRunner computes first-step NAI
        from scratch without seeding.

        Archives NAI history, sustainability metrics, and harvest summaries.

        Args:
            runner: DynamicStandardRunner that has completed run_flux_scenarios().

        Returns:
            DynamicSimulationResult or None if final state is unavailable.
        """
        cbm_vars = runner.get_final_cbm_vars()
        sit = runner.get_sit()

        if cbm_vars is None or sit is None:
            print("Warning: final state not available, skipping dynamic continuation")
            return None

        base_year = runner.forest_end_year

        # Seed first-timestep harvest from prior flux (only relevant when years>0)
        initial_species_nai = self._extract_initial_species_nai(cbm_vars)

        loader = Loader()
        disturbance_timing = loader.disturbance_time()

        dynamic_runner = DynamicRunner(
            harvest_ratio=self.df_data_manager.get_harvest_ratio(),
            clearfell_thinning_split=self.df_data_manager.get_clearfell_thinning_split(),
            disturbance_timing=disturbance_timing,
            scheduled_disturbances=self.df_data_manager.get_scheduled_disturbances(),
            species_column=self.df_data_manager.get_species_column(),
        )

        # Settle the AF backward-spinup DOM pools before recording output.
        # Without this, the freshly-spun Litter/Deadwood pools decay sharply over
        # the first ~3 timesteps, producing spurious negative flux at the start of
        # the series. Only applies to this user-CSV spinup path; the FM/AF 2070
        # continuation leaves it at 0. Overridable via dynamic_config.
        warmup_steps = 0
        if base_year == runner.calibration_year:
            # Pure-NAI mode (years=0): DynamicRunner produces the whole series, so
            # the spinup artefact lands in the output and must be warmed up here.
            warmup_steps = self.df_data_manager.get_spinup_warmup_steps(default=3)

        result = dynamic_runner.run_from_state(
            initial_cbm_vars=cbm_vars,
            sit=sit,
            years=self.df_data_manager.get_dynamic_years(),
            base_year=base_year,
            initial_species_nai=initial_species_nai,
            spinup_warmup_steps=warmup_steps,
        )

        # Archive diagnostics
        if not result.nai_history.empty:
            self.archive.store_dataframe(
                'standard_dynamic_nai_history',
                result.nai_history,
            )

        if not result.sustainability_metrics.empty:
            self.archive.store_dataframe(
                'standard_dynamic_sustainability_metrics',
                result.sustainability_metrics,
            )

        if result.harvest_summary:
            if 'disturbance_summary' in result.harvest_summary:
                self.archive.store_dataframe(
                    'dynamic_standard_disturbance_summary',
                    result.harvest_summary['disturbance_summary'],
                    scenario=self.scenario,
                )
            if 'nai_summary' in result.harvest_summary:
                self.archive.store_dataframe(
                    'dynamic_standard_nai_summary',
                    result.harvest_summary['nai_summary'],
                    scenario=self.scenario,
                )

        return result

    def _extract_initial_species_nai(self, cbm_vars) -> Optional[dict]:
        """
        Extract per-species harvest density (tC/ha) from last cbm_vars.flux.

        Returns None when no harvest occurred (e.g., years=0 — no seeding needed).
        When years>0, seeds first DynamicRunner timestep to avoid transition spike.

        Args:
            cbm_vars: CBMVariables from DynamicStandardRunner.get_final_cbm_vars().

        Returns:
            Dict mapping species_id -> harvest tC/ha, or None.
        """
        try:
            flux_df = cbm_vars.flux.to_pandas()
            classifiers_df = cbm_vars.classifiers.to_pandas()
            species_col = self.df_data_manager.get_species_column()

            harvest_flux = pd.Series(0.0, index=range(len(flux_df)))
            for col in ['DisturbanceSoftProduction', 'DisturbanceHardProduction',
                        'DisturbanceDOMProduction']:
                if col in flux_df.columns:
                    harvest_flux += flux_df[col].values

            if species_col in classifiers_df.columns and harvest_flux.sum() > 0:
                harvest_ratio = self.df_data_manager.get_harvest_ratio()
                species_ids = classifiers_df[species_col].values
                result = {}
                for sp_id in pd.unique(species_ids):
                    mask = species_ids == sp_id
                    sp_harvest = float(harvest_flux[mask].sum())
                    if sp_harvest > 0:
                        result[sp_id] = sp_harvest / harvest_ratio
                return result or None
        except Exception as e:
            print(f"Warning: Could not extract harvest flux for seeding: {e}")
        return None

    def _stock_to_flux(self, stock_df: pd.DataFrame, scenario: int) -> pd.DataFrame:
        """
        Convert stock data to flux (year-over-year differences).

        The first stock row (t=0, inherited state from spinup or static phase)
        serves as the baseline for differencing. The resulting flux DataFrame
        has one fewer row than the stock.

        Each flux row is labelled with the *later* (upper) stock row's year, so a
        year's flux is the change that occurred during that year
        (``stock[i] - stock[i-1]`` labelled ``Year(i)``). This matches
        ``cbm_scenario_fluxes()`` and the main DynamicScenarioGenerator, so the
        series starts at ``base_year + 1`` with no calibration-year placeholder row.

        Args:
            stock_df: DataFrame with Year, AGB, BGB, Deadwood, Litter,
                      Soil, Harvest, Total Ecosystem columns.
            scenario: Scenario number to assign.

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

    def get_dynamic_result(self) -> Optional[DynamicSimulationResult]:
        """
        Return the DynamicSimulationResult from the last run.

        Contains NAI history, harvest history, sustainability metrics.
        For diagnostic use.

        Returns:
            DynamicSimulationResult or None if not yet run.
        """
        return self._dynamic_result
