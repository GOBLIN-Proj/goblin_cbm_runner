"""
Resource Manager Module
=======================
Provides data loading, management, and utilities for CBM Runner.

Submodules:
- loaders: Database table access (Loader, AFLoader, FMLoader, SCLoader)
- managers: Configuration and data managers
- utils: Path management, parsing, scenario data fetching

For convenience, commonly used classes are exported at the top level.
"""
# Loaders
from goblin_cbm_runner.resource_manager.loaders import (
    Loader,
    LoaderBase,
    AFLoader,
    FMLoader,
    SCLoader,
)

# Managers
from goblin_cbm_runner.resource_manager.managers import (
    DataManager,
    DataManagerBase,
    AFDataManager,
    FMDataManager,
    SCDataManager,
    DFDataManager,
    Pools,
    FluxManager,
)

# Utils
from goblin_cbm_runner.resource_manager.utils import (
    Paths
)

__all__ = [
    # Loaders
    "Loader",
    "LoaderBase",
    "AFLoader",
    "FMLoader",
    "SCLoader",
    # Managers
    "DataManager",
    "DataManagerBase",
    "AFDataManager",
    "FMDataManager",
    "SCDataManager",
    "DFDataManager",
    "Pools",
    "FluxManager",
    # Utils
    "Paths"
]
