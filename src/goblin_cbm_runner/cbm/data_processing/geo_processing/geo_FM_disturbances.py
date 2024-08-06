"""
Geo Disturbances Module
=======================
This module manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios
involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes
disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

"""
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_inventory import Inventory
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_disturbance_utils import GeoDisturbUtils
import pandas as pd
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
        disturbance_dataframe (DataFrame): Central repository of disturbance event data.
        scenario_disturbance_dict (dict): Holds scenario-specific disturbance information.
        legacy_disturbance_dict (dict): Stores information on disturbances in legacy forests.
        yield_name_dict (dict): Maps yield classes to their corresponding names for easier reference.

    Parameters:
        config_path (str): Path to the configuration file guiding the simulation setup.
        calibration_year (int): Reference year from which simulation data is calibrated.
        forest_end_year (int): Designated end year for the simulation's forest data.
        afforestation_data (DataFrame): Data detailing afforestation projects, including species and area.
        scenario_data (DataFrame): Data defining various simulation scenarios.

    Methods:

        fill_baseline_forest():
            Populates disturbance data for the baseline forest, considering historical disturbances.
    
    """
    
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        scenario_data
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
        
        self.loader_class = Loader()
        self.data_manager_class = GeoDataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
        )

        self.utils_class = GeoDisturbUtils(
            config_path, calibration_year,forest_end_year, scenario_data
        )
        self.forest_baseline_year = self.data_manager_class.get_forest_baseline_year()

        self.afforestation_data = afforestation_data

        self.inventory_class = Inventory(
            calibration_year, config_path, scenario_data, afforestation_data
        )

        self.disturbance_timing = self.loader_class.disturbance_time()


    def fill_baseline_forest(self):
        """
        Fills the baseline (managed) forest with disturbance data.

        Returns:
            pandas.DataFrame: DataFrame containing disturbance data.
        """

        disturbance_df = self.utils_class.disturbance_structure()

        legacy_years = self.forest_end_year  - self.forest_baseline_year

        years = list(
            range(1, (legacy_years + 1))
        )

        disturbance_timing = self.disturbance_timing 

        data = []

        tracker = AfforestationTracker()

        self.utils_class.legacy_disturbance_tracker(self.inventory_class,tracker, years)

        for yr in years:
            for stand in tracker.disturbed_stands:
                if stand.year == yr:
                    
                    row_data = self.utils_class._generate_row(stand.species, "L", stand.soil, stand.yield_class, stand.dist, yr)

                    context = {"forest_type":"L",
                                "species":stand.species,
                                "yield_class":stand.yield_class,
                                "area":stand.area,
                                "dist":stand.dist,}
                    dataframes = {"disturbance_timing":disturbance_timing}

                    self.utils_class._process_scenario_row_data(row_data,context, dataframes)

                    data.append(row_data)

        disturbance_df = pd.DataFrame(data)
        disturbance_df = self.utils_class._drop_zero_area_rows(disturbance_df)

        return disturbance_df


