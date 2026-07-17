"""
Paths Module
============
Directory and path management for CBM simulation input data.

Provides paths for:
- Input data directories (AF_input, FM_input, SC_input)
- AIDB (Archive Index Database) location
- SIT data loading (via libcbm)

v0.6.0: Simplified to essential methods only.
"""
import os
import goblin_cbm_runner.database as aidb_path

from goblin_cbm_runner import get_local_dir
from libcbm.input.sit import sit_cbm_factory


class Paths:
    """
    Manages directory paths for CBM simulation input data.

    All input data is stored under: <package_dir>/data/<runner>_input/
    - AF_input: Afforestation baseline inputs
    - FM_input: Forest Management baseline inputs
    - SC_input: Scenario inputs
    """

    def __init__(self, sit_path=None, gen_baseline=False):
        """
        Initialize paths manager.

        Args:
            sit_path: External path (currently unused in v0.6.0)
            gen_baseline: Whether generating baseline (currently unused in v0.6.0)
        """
        self.external_path = sit_path
        self.gen_baseline = gen_baseline

    # =========================================================================
    # SHARED METHODS
    # =========================================================================

    def make_base_data_dir(self):
        """Create the base data directory."""
        os.makedirs(os.path.join(get_local_dir(), "data"), exist_ok=True)

    def get_aidb_path(self):
        """
        Get path to the AIDB (Archive Index Database).

        Returns:
            str: Path to ireland_cbm_defaults_v6.1.db
        """
        return os.path.join(aidb_path.get_local_dir(), "ireland_cbm_defaults_v6.1.db")

    # =========================================================================
    # AF (AFFORESTATION) METHODS
    # =========================================================================

    def make_AF_input_data_dir(self):
        """Create AF input data directory."""
        os.makedirs(os.path.join(get_local_dir(), "data", "AF_input"), exist_ok=True)

    def clean_AF_input_data_dir(self):
        """Remove all files from AF input data directory."""
        af_path = os.path.join(get_local_dir(), "data", "AF_input")
        if os.path.exists(af_path):
            for file in os.listdir(af_path):
                file_path = os.path.join(af_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def get_AF_input_data_dir(self):
        """Get AF input data directory path."""
        return os.path.join(get_local_dir(), "data", "AF_input")

    def set_AF_SIT_data_dir(self, path, db_path):
        """
        Load SIT configuration and initialize inventory for AF.

        Args:
            path: Path to input data directory containing sit_config.json
            db_path: Path to AIDB database

        Returns:
            tuple: (sit, classifiers, inventory)
        """
        sit_config_path = os.path.join(path, "sit_config.json")
        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)
        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
        return sit, classifiers, inventory

    # =========================================================================
    # FM (FOREST MANAGEMENT) METHODS
    # =========================================================================

    def make_FM_input_data_dir(self):
        """Create FM input data directory."""
        os.makedirs(os.path.join(get_local_dir(), "data", "FM_input"), exist_ok=True)

    def clean_FM_input_data_dir(self):
        """Remove all files from FM input data directory."""
        fm_path = os.path.join(get_local_dir(), "data", "FM_input")
        if os.path.exists(fm_path):
            for file in os.listdir(fm_path):
                file_path = os.path.join(fm_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def get_FM_input_data_dir(self):
        """Get FM input data directory path."""
        return os.path.join(get_local_dir(), "data", "FM_input")

    def set_FM_SIT_data_dir(self, path, db_path):
        """
        Load SIT configuration and initialize inventory for FM.

        Args:
            path: Path to input data directory containing sit_config.json
            db_path: Path to AIDB database

        Returns:
            tuple: (sit, classifiers, inventory)
        """
        sit_config_path = os.path.join(path, "sit_config.json")
        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)
        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
        return sit, classifiers, inventory

    def set_FM_spinup_SIT_data_dir(self, path, db_path):
        """
        Load spinup SIT configuration for FM (uses standing volume).

        Args:
            path: Path to input data directory containing spinup_config.json
            db_path: Path to AIDB database

        Returns:
            tuple: (sit, classifiers, inventory)
        """
        sit_config_path = os.path.join(path, "spinup_config.json")
        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)
        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
        return sit, classifiers, inventory

    # =========================================================================
    # SC (SCENARIO) METHODS
    # =========================================================================

    def make_SC_input_data_dir(self):
        """Create SC input data directory."""
        os.makedirs(os.path.join(get_local_dir(), "data", "SC_input"), exist_ok=True)

    def clean_SC_input_data_dir(self):
        """Remove all files from SC input data directory."""
        sc_path = os.path.join(get_local_dir(), "data", "SC_input")
        if os.path.exists(sc_path):
            for file in os.listdir(sc_path):
                file_path = os.path.join(sc_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def get_SC_input_data_dir(self):
        """Get SC input data directory path."""
        return os.path.join(get_local_dir(), "data", "SC_input")

    def set_SC_SIT_data_dir(self, path, db_path):
        """
        Load SIT configuration and initialize inventory for SC.

        Args:
            path: Path to input data directory containing sit_config.json
            db_path: Path to AIDB database

        Returns:
            tuple: (sit, classifiers, inventory)
        """
        sit_config_path = os.path.join(path, "sit_config.json")
        sit = sit_cbm_factory.load_sit(sit_config_path, db_path)
        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
        return sit, classifiers, inventory
