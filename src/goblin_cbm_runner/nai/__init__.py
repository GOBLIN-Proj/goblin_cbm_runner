"""
NAI Module
==========
Net Annual Increment calculation and NAI-based harvest scheduling.

Components:
- NAICalculator: Calculate NAI from pool data
- HarvestScheduler: Determine harvest targets from NAI (with disturbance timing)
- DynamicRunner: Stepwise simulation with NAI-based harvest
- ScheduledDisturbance: Non-harvest disturbance events (fire, wind, etc.)
- DynamicSimulationResult: Results container

See refactor/NAI_IMPLEMENTATION_PLAN.md for design details.
"""
from goblin_cbm_runner.nai.nai_calculator import NAICalculator
from goblin_cbm_runner.nai.harvest_scheduler import HarvestScheduler
from goblin_cbm_runner.nai.dynamic_runner import (
    DynamicRunner,
    ScheduledDisturbance,
    DynamicSimulationResult
)

__all__ = [
    'NAICalculator',
    'HarvestScheduler',
    'DynamicRunner',
    'ScheduledDisturbance',
    'DynamicSimulationResult'
]
