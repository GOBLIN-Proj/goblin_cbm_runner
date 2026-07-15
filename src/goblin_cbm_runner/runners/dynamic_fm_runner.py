"""
Dynamic FM Runner
=================
Extends FMRunner with state capture for NAI-based continuation.

This runner is identical to FMRunner but exposes the final CBMVariables
and SIT after simulation, enabling DynamicRunner to continue the
simulation beyond the FM end year (e.g., post-2070).

Usage:
    from goblin_cbm_runner.runners.dynamic_fm_runner import DynamicFMRunner
    from goblin_cbm_runner.resource_manager import FMDataManager

    fm_runner = DynamicFMRunner(data_manager=FMDataManager())
    fm_runner.generate_input_data()
    fm_results = fm_runner.run_flux_scenarios()

    # Now extract state for DynamicRunner
    cbm_vars = fm_runner.get_final_cbm_vars()
    sit = fm_runner.get_sit()

Note:
    FMRunner itself is unchanged. DynamicFMRunner inherits all behavior
    and adds only the accessor methods for state capture.
"""
from goblin_cbm_runner.runners.fm_runner import FMRunner


class DynamicFMRunner(FMRunner):
    """
    FM Runner with state capture for NAI-based continuation.

    Identical to FMRunner, but provides access to the final CBMVariables
    and SIT objects after simulation completes. These are needed by
    DynamicRunner.run_from_state() to continue the simulation.

    The state capture itself happens in CBMSim (cbm_methods.py), which
    stores cbm_vars and step_sit after the FM step loop. This class
    just exposes those stored references.
    """

    def get_final_cbm_vars(self):
        """
        Get the final CBMVariables from the last FM simulation.

        Returns the state after the last timestep, suitable for passing
        to DynamicRunner.run_from_state() for post-2070 continuation.

        Returns:
            CBMVariables or None: Final state if simulation has been run, else None.
        """
        return self.cbm_sim.get_final_cbm_vars()

    def get_sit(self):
        """
        Get the SIT used in the last FM step loop.

        Returns the SIT configuration (growth curves, AIDB reference) needed
        by DynamicRunner to continue the simulation.

        Returns:
            SIT or None: SIT object if simulation has been run, else None.
        """
        return self.cbm_sim.get_last_sit()
