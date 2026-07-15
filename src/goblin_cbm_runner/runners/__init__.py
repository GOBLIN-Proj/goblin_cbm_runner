"""
Runners Module
==============
Contains runner classes for AF, FM, and SC simulations.

Each runner is responsible for:
1. Generating input data (CSV files)
2. Running CBM simulation
3. Returning results

Runners:
- AFRunner: Historic afforestation baseline (1990-2070)
- FMRunner: Forest management baseline (2016-2070)
- SCRunner: Future afforestation scenarios (2020-2070)
- StandardRunner: General-purpose runner for custom scenarios
"""

from goblin_cbm_runner.runners.af_runner import AFRunner
from goblin_cbm_runner.runners.fm_runner import FMRunner
from goblin_cbm_runner.runners.sc_runner import SCRunner
from goblin_cbm_runner.runners.standard_runner import StandardRunner

__all__ = ['AFRunner', 'FMRunner', 'SCRunner', 'StandardRunner']
