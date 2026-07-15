"""
Dynamic Standard Runner
=======================
Extends StandardRunner with state capture for NAI-based continuation.

Overrides run_flux_scenarios() to use AF_simulate_stock (manual spinup+step,
stores _last_cbm_vars) instead of cbm_aggregate_scenario_stock (black-box,
no state storage). This makes get_final_cbm_vars() and get_sit() available
for DynamicRunner continuation.

Key behaviour — years=0 (NAI from day 1):
    AF_simulate_stock calls spinup then loops for range(1, years+1).
    With years=0 the loop is empty — only spinup fires.
    _last_cbm_vars = initial pool state from spinup.
    DynamicRunner starts NAI from this state. No transition spike.

Key behaviour — years > 0 (static warm-up then NAI):
    Static disturbance schedule runs first; DynamicRunner continues after.
    disturbance_events.csv must contain a valid schedule.

Default end_year:
    DynamicStandardRunner defaults end_year to baseline_year (years=0),
    matching the "NAI from day 1" use case. StandardRunner defaults to 2050.
    Override end_year in config to add a static warm-up period.

Usage:
    runner = DynamicStandardRunner(
        csv_directory='./my_forest/',
        config={'baseline_year': 2020},   # end_year defaults to baseline_year
    )
    runner.generate_input_data()
    static_flux = runner.run_flux_scenarios()   # empty DataFrame (years=0)
    cbm_vars = runner.get_final_cbm_vars()      # spinup state
    sit = runner.get_sit()
"""
import pandas as pd

from goblin_cbm_runner.runners.standard_runner import StandardRunner


class DynamicStandardRunner(StandardRunner):
    """
    StandardRunner with state capture for NAI-based continuation.

    Overrides run_flux_scenarios() to use AF_simulate_stock instead of the
    black-box cbm_aggregate_scenario_stock. This stores _last_cbm_vars and
    _last_sit in CBMSim after every run, enabling DynamicRunner continuation.

    Default end_year is baseline_year (years=0) so that the static phase is
    skipped and DynamicRunner starts from spinup state — "NAI from day 1".
    Set end_year > baseline_year in config to add a static warm-up period.
    """

    def __init__(self, csv_directory: str, config: dict = None, scenario: int = 0):
        """
        Initialize DynamicStandardRunner.

        Args:
            csv_directory: Path to directory containing required SIT CSV files.
            config: Optional overrides. Keys:
                - 'baseline_year' (int): Start year (default 2020)
                - 'end_year' (int): End year (default = baseline_year, i.e. years=0)
            scenario: Scenario number for output labelling (default 0).
        """
        _config = config or {}
        baseline_year = _config.get("baseline_year", 2020)
        # Default end_year to baseline_year so years=0 (NAI from day 1)
        if "end_year" not in _config:
            _config = dict(_config)
            _config["end_year"] = baseline_year

        super().__init__(
            csv_directory=csv_directory,
            config=_config,
            scenario=scenario,
        )

    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Run simulation using AF_simulate_stock for state capture.

        Uses AF_simulate_stock (manual spinup+step) instead of the black-box
        cbm_aggregate_scenario_stock. After this method completes,
        get_final_cbm_vars() and get_sit() return valid objects for
        DynamicRunner continuation.

        With years=0 (default): only spinup fires; returns empty DataFrame.
        With years > 0: static disturbance schedule runs; returns flux DataFrame.

        Returns:
            pd.DataFrame: Carbon flux data (empty if years=0).
        """
        self.logger.info(
            f"Starting DynamicStandard simulation (scenario {self.scenario}, "
            f"{self.calibration_year}–{self.forest_end_year}, years={self.years})..."
        )

        forest_data = self.cbm_sim.AF_simulate_stock(
            self.scenario,
            self._load_sit,
            self.years,
            self.year_range,
            self._get_input_dir,
            self.paths.get_aidb_path,
        )

        return self.cbm_sim.cbm_scenario_fluxes(forest_data)

    def get_final_cbm_vars(self):
        """
        Get the final CBMVariables from the last simulation.

        With years=0: returns spinup state (initial pool state).
        With years > 0: returns state after the last static timestep.

        Returns:
            CBMVariables or None: Final state if simulation has been run.
        """
        return self.cbm_sim.get_final_cbm_vars()

    def get_sit(self):
        """
        Get the SIT used in the last simulation.

        Returns the SIT configuration (growth curves, AIDB reference) needed
        by DynamicRunner to continue the simulation.

        Returns:
            SIT or None: SIT object if simulation has been run, else None.
        """
        return self.cbm_sim.get_last_sit()
