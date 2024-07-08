"""
Paths module
=============
This module contains the Paths class, which is used to set up the necessary directory paths for CBM simulation input data for cbm_runner and geo_cbm_runner.
"""
import os 
import time
import goblin_cbm_runner.database as aidb_path
import goblin_cbm_runner.default_runner.generated_input_data as runner_input_data_path
import goblin_cbm_runner.default_runner.baseline_input_conf as runner_baseline_conf_path
import goblin_cbm_runner.geo_cbm_runner.generated_input_data as geo_runner_input_data_path
import goblin_cbm_runner.geo_cbm_runner.baseline_input_conf as geo_runner_baseline_conf_path
import goblin_cbm_runner.forest_sim.generated_input_data as forest_runner_input_data_path
import goblin_cbm_runner.forest_sim.baseline_input_conf as forest_runner_baseline_conf_path
import goblin_cbm_runner.historic_affor.baseline_input_conf as historic_affor_baseline_conf_path
import goblin_cbm_runner.historic_affor.generated_input_data as historic_affor_input_data_path

class Paths:
    """
    This class is responsible for setting up the necessary directory paths for CBM simulation input data for cbm_runner and geo_cbm_runner.

    Attributes:
        external_path (str): The specific site path provided by the user; None if not provided.
        gen_baseline (bool): A boolean indicating whether to generate baseline input data.


    Methods:
        setup_runner_paths: Sets up the necessary directory paths for CBM simulation input data for cbm_runner.
        setup_geo_runner_paths: Sets up the necessary directory paths for CBM simulation input data for geo_cbm_runner.
        make_external_dirs: Creates directories for external use.
        get_generated_input_data_path: Returns the generated input data path.
        get_baseline_conf_path: Returns the baseline configuration path.
        get_internal_runner_generated_input_data_path: Returns the internal generated input data path.
        get_internal_runner_baseline_conf_path: Returns the internal baseline configuration path.
        get_internal_geo_runner_generated_input_data_path: Returns the internal generated input data path for geo_cbm_runner.
        get_internal_geo_runner_baseline_conf_path: Returns the internal baseline configuration path for geo_cbm_runner.
        get_internal_forest_runner_generated_input_data_path: Returns the internal generated input data path for forest_sim.
        get_internal_forest_runner_baseline_conf_path: Returns the internal baseline configuration path for forest_sim.
        get_internal_historic_affor_generated_input_data_path: Returns the internal generated input data path for historic_affor.
        get_internal_historic_affor_baseline_conf_path: Returns the internal baseline configuration path for historic_affor.
        is_path_internal: Determines whether the provided path is one of the internally generated paths.
        get_aidb_path: Returns the path to the AIDB directory.
        retry_operation: Retry a function multiple times if it fails.
    """
    def __init__(self, sit_path, gen_baseline):
        self.external_path = sit_path
        self.gen_baseline = gen_baseline

        self.generated_input_data_path = None
        self.baseline_conf_path = None

    def setup_runner_paths(self, sit_path):
        """
        Sets up the necessary directory paths for CBM simulation input data for cbm_runner.
        Args:
            sit_path (str): The specific site path provided by the user; None if not provided.
        Returns:
            None
        """
        # Initialize default paths before checking sit_path
        path = os.path.join(sit_path, "CBM/generated_input_data") if sit_path else runner_input_data_path.get_local_dir()
        baseline_conf_path = os.path.join(sit_path, "CBM/baseline_input_conf") if sit_path and self.gen_baseline else runner_baseline_conf_path.get_local_dir() if self.gen_baseline else None

        if sit_path is not None:
            self.make_external_dirs(sit_path)  # Only pass sit_path, since make_external_dirs expects one argument

        self.generated_input_data_path = path
        self.baseline_conf_path = baseline_conf_path

    def setup_geo_runner_paths(self, sit_path):
        """
        Sets up the necessary directory paths for CBM simulation input data for geo_cbm_runner.


        Args:
            sit_path (str): The specific site path provided by the user; None if not provided.

        Returns:
            None
        """
        # Initialize default paths before checking sit_path
        path = os.path.join(sit_path, "CBM/generated_input_data") if sit_path else geo_runner_input_data_path.get_local_dir()
        baseline_conf_path = os.path.join(sit_path, "CBM/baseline_input_conf") if sit_path and self.gen_baseline else geo_runner_baseline_conf_path.get_local_dir() if self.gen_baseline else None


        if sit_path is not None:
            self.make_external_dirs(sit_path)  # Only pass sit_path, since make_external_dirs expects one argument

        self.generated_input_data_path = path
        self.baseline_conf_path = baseline_conf_path


    def setup_forest_runner_paths(self, sit_path):
        """
        Sets up the necessary directory paths for CBM simulation input data for forest_sim.


        Args:
            sit_path (str): The specific site path provided by the user; None if not provided.

        Returns:
            None
        """
        # Initialize default paths before checking sit_path
        path = os.path.join(sit_path, "CBM/generated_input_data") if sit_path else forest_runner_input_data_path.get_local_dir()
        baseline_conf_path = os.path.join(sit_path, "CBM/baseline_input_conf") if sit_path and self.gen_baseline else forest_runner_baseline_conf_path.get_local_dir() if self.gen_baseline else None


        if sit_path is not None:
            self.make_external_dirs(sit_path)

        self.generated_input_data_path = path
        self.baseline_conf_path = baseline_conf_path


    def setup_historic_affor_paths(self, sit_path):
        """
        Sets up the necessary directory paths for CBM simulation input data for historic_affor.

        Args:
            sit_path (str): The specific site path provided by the user; None if not provided.

        Returns:
            None
        """

        path = os.path.join(sit_path, "CBM/generated_input_data") if sit_path else historic_affor_input_data_path.get_local_dir()
        baseline_conf_path = os.path.join(sit_path, "CBM/baseline_input_conf") if sit_path and self.gen_baseline else historic_affor_baseline_conf_path.get_local_dir() if self.gen_baseline else None

        if sit_path is not None:
            self.make_external_dirs(sit_path)

        self.generated_input_data_path = path
        self.baseline_conf_path = baseline_conf_path
        

    def make_external_dirs(self, path):
        """
        Creates directories for external use.

        Args:
            path (str): The directory path.

        Returns:
            None
        """
        os.makedirs(os.path.join(path, "CBM/generated_input_data"), exist_ok=True)

        if self.gen_baseline:
            os.makedirs(os.path.join(path, "CBM/baseline_input_conf"), exist_ok=True)


    def get_generated_input_data_path(self):
        """
        Returns the generated input data path.

        Returns:
            str: The generated input data path.
        """
        return self.generated_input_data_path
    
    def get_baseline_conf_path(self):
        """
        Returns the baseline configuration path.

        Returns:
            str: The baseline configuration path.
        """
        return self.baseline_conf_path
    
    

    def get_internal_runner_generated_input_data_path(self):
        """
        Returns the internal generated input data path.

        Returns:
            str: The internal generated input data path.
        """
        return runner_input_data_path.get_local_dir()
    
    def get_internal_runner_baseline_conf_path(self):
        """
        Returns the internal baseline configuration path.

        Returns:
            str: The internal baseline configuration path.
        """
        return runner_baseline_conf_path.get_local_dir()
    
    def get_internal_geo_runner_generated_input_data_path(self):
        """
        Returns the internal generated input data path for geo_cbm_runner.

        Returns:
            str: The internal generated input data path for geo_cbm_runner.
        """
        return geo_runner_input_data_path.get_local_dir()
    
    
    def get_internal_geo_runner_baseline_conf_path(self):
        """
        Returns the internal baseline configuration path for geo_cbm_runner.

        Returns:
            str: The internal baseline configuration path for geo_cbm_runner.
        """
        return geo_runner_baseline_conf_path.get_local_dir()
    

    def get_internal_forest_runner_generated_input_data_path(self):
        """
        Returns the internal generated input data path for forest_sim.

        Returns:
            str: The internal generated input data path for forest_sim.
        """
        return forest_runner_input_data_path.get_local_dir()
    
    def get_internal_forest_runner_baseline_conf_path(self):
        """
        Returns the internal baseline configuration path for forest_sim.

        Returns:
            str: The internal baseline configuration path for forest_sim.
        """
        return forest_runner_baseline_conf_path.get_local_dir()
    
    def get_internal_historic_affor_generated_input_data_path(self):
        """
        Returns the internal generated input data path for historic_affor.

        Returns:
            str: The internal generated input data path for historic_affor.
        """
        return historic_affor_input_data_path.get_local_dir()
    
    def get_internal_historic_affor_baseline_conf_path(self):
        """
        Returns the internal baseline configuration path for historic_affor.

        Returns:
            str: The internal baseline configuration path for historic_affor.
        """
        return historic_affor_baseline_conf_path.get_local_dir()

    def is_path_internal(self, path):
        """
        Determines whether the provided path is one of the internally generated paths.
        
        Args:
            path (str): The path to check.
            
        Returns:
            bool: True if the path is internally generated, False otherwise.
        """
        internal_paths = [
            self.get_internal_runner_baseline_conf_path(),
            self.get_internal_runner_generated_input_data_path(),
            self.get_internal_geo_runner_baseline_conf_path(),
            self.get_internal_geo_runner_generated_input_data_path(),
            self.get_internal_forest_runner_baseline_conf_path(),
            self.get_internal_forest_runner_generated_input_data_path(),
            self.get_internal_historic_affor_baseline_conf_path(),
            self.get_internal_historic_affor_generated_input_data_path(),
        ]
        # Check if the provided path matches any of the internal paths
        return path in internal_paths
    
    def get_aidb_path(self):
        """
        Returns the path to the AIDB directory.

        Returns:
            str: The path to the AIDB directory.
        """
        return os.path.join(aidb_path.get_local_dir(), "ireland_cbm_defaults_v4.db")

    def retry_operation(self, function, max_attempts=5, wait_time=60):
        """
        Retry a function multiple times if it fails.

        Args:
            function (function): The function to execute.
            max_attempts (int): The maximum number of attempts.
            wait_time (int): The time to wait before retrying.

        Returns:
            The result of the function if successful.
        """
        for attempt in range(max_attempts):
            try:
                return function()  # Attempt to execute the function
            except Exception as e:
                print(f"Attempt {attempt + 1} failed due to error: {e}")
                time.sleep(wait_time)  # Wait before retrying
        raise Exception(f"All {max_attempts} attempts failed.")