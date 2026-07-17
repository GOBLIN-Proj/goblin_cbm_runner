"""
Dynamic AF Runner
=================
Extends AFRunner with state capture for NAI-based continuation.

Unlike DynamicFMRunner (which inherits FMRunner's state-capturing methods
unchanged), DynamicAFRunner must override run_flux_scenarios() because
AFRunner's default methods (cbm_aggregate_scenario_stock, cbm_comprehensive_simulation)
use the black-box cbm_simulator.simulate() approach, which never stores
_last_cbm_vars.

This override swaps in AF_simulate_stock and AF_comprehensive_simulation,
which use manual spinup+step and store _last_cbm_vars for DynamicRunner
continuation.

Usage:
    from goblin_cbm_runner.runners.dynamic_af_runner import DynamicAFRunner
    from goblin_cbm_runner.resource_manager import AFDataManager

    af_runner = DynamicAFRunner(data_manager=AFDataManager())
    af_runner.generate_input_data()
    af_results = af_runner.run_flux_scenarios()

    # Now extract state for DynamicRunner
    cbm_vars = af_runner.get_final_cbm_vars()  # Not None!
    sit = af_runner.get_sit()
"""
import pandas as pd
from goblin_cbm_runner.runners.af_runner import AFRunner


class DynamicAFRunner(AFRunner):
    """
    AF Runner with state capture for NAI-based continuation.

    Overrides run_flux_scenarios() to use AF_simulate_stock (lightweight)
    or AF_comprehensive_simulation (comprehensive) instead of the black-box
    methods. These manual spinup+step methods store _last_cbm_vars and
    _last_sit in CBMSim, making get_final_cbm_vars() and get_sit() work.

    Why the override is needed:
        AFRunner uses cbm_aggregate_scenario_stock / cbm_comprehensive_simulation,
        which call cbm_simulator.simulate() internally. That function handles
        spinup+stepping as a black box and never exposes the final CBMVariables.

        FMRunner uses FM_simulate_stock / FM_comprehensive_simulation, which
        already use manual spinup+step and store state. So DynamicFMRunner
        does NOT need this override.
    """

    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Run AF simulation using state-capturing methods.

        Uses AF_simulate_stock (lightweight) or AF_comprehensive_simulation
        (comprehensive) instead of the black-box methods. After this method
        completes, get_final_cbm_vars() and get_sit() will return valid objects.

        Returns:
            pd.DataFrame: Aggregated carbon flux data for AF baseline.
        """
        forest_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        if self.comprehensive:
            result = self.cbm_sim.AF_comprehensive_simulation(
                self.SCENARIO,
                self.paths.set_AF_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_AF_input_data_dir,
                self.paths.get_aidb_path
            )
            forest_data = result['aggregated']
            self.last_validation_tables = result['validation']
        else:
            forest_data = self.cbm_sim.AF_simulate_stock(
                self.SCENARIO,
                self.paths.set_AF_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_AF_input_data_dir,
                self.paths.get_aidb_path
            )
            self.last_validation_tables = None

        fluxes_data = self.cbm_sim.cbm_scenario_fluxes(forest_data)

        fluxes_forest_data = pd.concat(
            [fluxes_forest_data, fluxes_data], ignore_index=True
        )

        return fluxes_forest_data

    def get_final_cbm_vars(self):
        """
        Get the final CBMVariables from the last AF simulation.

        Returns the state after the last timestep, suitable for passing
        to DynamicRunner.run_from_state() for post-2070 continuation.

        Returns:
            CBMVariables or None: Final state if simulation has been run, else None.
        """
        return self.cbm_sim.get_final_cbm_vars()

    def get_sit(self):
        """
        Get the SIT used in the last AF step loop.

        Returns the SIT configuration (growth curves, AIDB reference) needed
        by DynamicRunner to continue the simulation.

        Returns:
            SIT or None: SIT object if simulation has been run, else None.
        """
        return self.cbm_sim.get_last_sit()
