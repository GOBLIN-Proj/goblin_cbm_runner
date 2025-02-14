"""
Geo Disturbances Module
=======================
This module manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios
involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes
disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

"""
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_inventory import Inventory
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_disturbance_utils import GeoDisturbUtils
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class FMDisturbances:
    """
    Manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios 
    involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes 
    disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

    Attributes:
        forest_end_year (int): Target end year for forest simulation data.
        calibration_year (int): Base year for data calibration within the simulation.
        loader_class (Loader): Instance responsible for loading external data resources.
        data_manager_class (DataManager): Manages retrieval and organization of simulation data.
        afforestation_data (DataFrame): Contains data on afforestation activities, including species and areas.
        inventory_class (Inventory): Manages the preparation and structuring of forest inventory data.
        disturbance_timing (DataFrame): Contains information on the timing and type of disturbances.
        scenario_disturbance_dict (dict): Holds scenario-specific disturbance information.
        FM_disturbance_dict (dict): Stores information on disturbances in forest management scenarios.
        full_rotation_scenario_years (int): Number of years for a full rotation scenario.

    Parameters:
        geo_data_manager (GeoDataManager): Instance responsible for managing geographical data.
    """
    
    def __init__(
        self,
        geo_data_manager,
    ):
        self.data_manager_class = geo_data_manager
        self.forest_end_year = self.data_manager_class.get_forest_end_year()
        self.calibration_year = self.data_manager_class.get_calibration_year()
        self.full_rotation_scenario_years = (self.forest_end_year - self.calibration_year) + 1
        
        self.loader_class = Loader()

        self.utils_class = GeoDisturbUtils(geo_data_manager)

        self.afforestation_data = self.data_manager_class.get_afforestation_data()

        self.inventory_class = Inventory(geo_data_manager)

        self.disturbance_timing = self.loader_class.disturbance_time()

        self.scenario_disturbance_dict = self.data_manager_class.get_scenario_disturbance_dict()

        self.FM_disturbance_dict = self.scenario_disturbance_dict[-1]


    def fill_baseline_forest(self):
        """
        Fills the baseline (managed) forest with disturbance data.

        Returns:
            pandas.DataFrame: DataFrame containing disturbance data for the baseline (managed) forest.
        """

        year_start = 1

        legacy_inventory_df = self.utils_class.legacy_disturbance_tracker(self.inventory_class,
                                                                          year_start)


        legacy_inventory_df = self.utils_class._drop_zero_area_rows(legacy_inventory_df)

        dist_tracker = AfforestationTracker(self.data_manager_class,
                                            self.FM_disturbance_dict,
                                            legacy_inventory_df, 
                                            self.full_rotation_scenario_years)

        FM_disturbance_df = dist_tracker.run_simulation()

        disturbance_df = self.utils_class.format_disturbance_data(FM_disturbance_df, self.disturbance_timing)

        return disturbance_df





