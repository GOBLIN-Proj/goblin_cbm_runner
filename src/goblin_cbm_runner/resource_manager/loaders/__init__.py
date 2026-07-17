"""
Loaders Module
==============
Data loaders for accessing database tables.

- Loader: Main facade (backward compatible)
- AFLoader: Afforestation baseline data
- FMLoader: Forest management baseline data
- SCLoader: Scenario data
"""
from goblin_cbm_runner.resource_manager.loaders.loader import Loader
from goblin_cbm_runner.resource_manager.loaders.base import LoaderBase
from goblin_cbm_runner.resource_manager.loaders.af_loader import AFLoader
from goblin_cbm_runner.resource_manager.loaders.fm_loader import FMLoader
from goblin_cbm_runner.resource_manager.loaders.sc_loader import SCLoader

__all__ = [
    "Loader",
    "LoaderBase",
    "AFLoader",
    "FMLoader",
    "SCLoader",
]
