"""
AF Disturbances Module
===================
This module is responsible for managing disturbances within a CBM (Carbon Budget Modeling) model.

It manages the creation of the disturbance input for legacy afforesation since 1990. 
"""
from goblin_cbm_runner.cbm.data_processing.default_processing.disturnance_utils import DisturbUtils
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.AF_inventory import AFInventory
import pandas as pd



class AFDisturbances:
    """
    Manages disturbances within a CBM (Carbon Budget Model) model, addressing both legacy and scenario-based disturbances. 
    This class plays a pivotal role in simulating the impact of disturbances on forest carbon stocks and fluxes, 
    adapting to user-defined management strategies and afforestation scenarios.

    Attributes:
        forest_end_year (int): The final year for simulation, defining the temporal boundary for scenario execution.
        calibration_year (int): The initial year for data calibration.
        loader_class (Loader): Instance of Loader for loading and processing data.
        data_manager_class (DataManager): Instance of DataManager for managing simulation data and configurations.
        utils_class (DisturbUtils): Instance of DisturbUtils for managing disturbance data.
        forest_baseline_year (int): The baseline year for afforestation data.
        scenario_forest_classifiers (dict): A dictionary containing classifiers for scenario-based forest data.
        afforestation_data (DataFrame): Detailed data of afforestation activities per scenario.
        inventory_class (Inventory): Instance of Inventory for managing forest inventory data.
        disturbance_timing (dict): A dictionary containing disturbance timing data.
        disturbance_dataframe (DataFrame): A DataFrame containing disturbance data.
        yield_name_dict (dict): A dictionary containing yield names for forest data.
        

    Parameters:
        config_path (str): Configuration path for setting up CBM simulations.
        calibration_year (int): The initial year for data calibration.
        forest_end_year (int): The final year for simulation, defining the temporal boundary for scenario execution.
        afforestation_data (DataFrame): Detailed data of afforestation activities per scenario.
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
        self.data_manager_class = DataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
        )
        self.utils_class = DisturbUtils(
            config_path, calibration_year,forest_end_year, scenario_data
        )
        self.forest_baseline_year = self.data_manager_class.get_afforestation_baseline()

        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.afforestation_data = afforestation_data
        self.inventory_class = AFInventory(
            calibration_year, config_path
        )

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.disturbance_dataframe = self.loader_class.disturbance_data()
        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()


    def legacy_disturbance_afforestation_area(self, years):
        """
        Calculates the afforestation area for legacy forest over a number of years from 1990.

        This afforestation data pertains to private afforestation in Ireland. 

        Parameters:
            years (int): The number of years to calculate afforestation for.

        Returns:
            DataFrame: A dataframe with calculated afforestation areas.
        """
        years = list(range(1, years + 1))

        result_dataframe = pd.DataFrame()

        classifiers = self.scenario_forest_classifiers
        year_index = self.data_manager_class.get_afforestation_baseline()

        afforestation_mineral = self.inventory_class.legacy_afforestation_annual()[
            "mineral_afforestation"
        ]
        afforestation_organic = self.inventory_class.legacy_afforestation_annual()[
            "peat_afforestation"
        ]


        yield_dict = self.data_manager_class.get_yield_baseline_dict()

        year_count = 0
        index = 0

        for species in classifiers["Species"].keys():
            if species in yield_dict.keys():
                for yield_class in yield_dict[species].keys():
                    for soil_class in classifiers["Soil classes"].keys():
                        for i in years:
                            result_dataframe.at[index, "year"] = year_count
                            result_dataframe.at[index, "species"] = species
                            result_dataframe.at[index, "yield_class"] = yield_class
                            result_dataframe.at[index, "soil"] = soil_class

                            if soil_class == "peat":
                                result_dataframe.at[
                                    index, "area_ha"
                                ] = afforestation_organic[year_index + year_count][
                                    species
                                ][
                                    yield_class
                                ]

                            else:
                                result_dataframe.at[
                                    index, "area_ha"
                                ] = afforestation_mineral[year_index + year_count][
                                    species
                                ][
                                    yield_class
                                ]

                            index += 1
                            year_count += 1

                        year_count = 0
        
        return result_dataframe


    def fill_baseline_forest(self):
        """
        Fills the disturbance data for legacy years based on the given configuration.

        Returns:
            pandas.DataFrame: The disturbance data for legacy years.
        """
        disturbances = self.data_manager_class.get_disturbances_config()["Scenario"]
        forest_baseline_year = self.data_manager_class.get_afforestation_baseline()
        yield_name_dict = self.yield_name_dict
        calibration_year = self.calibration_year
        target_year = self.forest_end_year
        disturbance_df = self.utils_class.disturbance_structure()

        legacy_years = (calibration_year - forest_baseline_year) + 1
        loop_years = (target_year - forest_baseline_year) + 1


        legacy_afforestation_inventory = self.legacy_disturbance_afforestation_area(legacy_years)
        disturbance_dataframe = self.disturbance_dataframe
        disturbance_timing = self.disturbance_timing
        data = []
        for yr in range(0, (loop_years + 1)):

            for dist in disturbances:
                if dist == "DISTID3":
                        species, forest_type, soil, yield_class = "?", "L", "?", "?"
                        row_data = self.utils_class._generate_row(species, forest_type, soil, yield_class, dist, yr+1)
                        context = {
                            "forest_type": "L",
                            "species": "?",
                            "soil": "?",
                            "yield_class": "?",
                            "dist": dist,
                            "year": yr,
                            "forest_baseline_year": forest_baseline_year,
                        }
                        dataframes = {
                            "legacy_afforestation_inventory": legacy_afforestation_inventory,
                            "disturbance_dataframe": disturbance_dataframe,
                            "disturbance_timing": disturbance_timing,
                        }
                        self.utils_class._process_row_data(row_data, context, dataframes)
                        data.append(row_data)
                else:    
                    for species in yield_name_dict.keys():
                        classifier_combo = self.utils_class._get_classifier_combinations(species, dist)
                        for combination in classifier_combo:
                            forest_type, soil, yield_class = combination
                            row_data = self.utils_class._generate_row(species, forest_type, soil, yield_class, dist, yr+1)
                            context = {
                                "forest_type": forest_type,
                                "species": species,
                                "soil": soil,
                                "yield_class": yield_class,
                                "dist": dist,
                                "year": yr,
                                "forest_baseline_year": forest_baseline_year,
                            }
                            dataframes = {
                                "legacy_afforestation_inventory": legacy_afforestation_inventory,
                                "disturbance_dataframe": disturbance_dataframe,
                                "disturbance_timing": disturbance_timing,
                            }
                            self.utils_class._process_row_data(row_data, context, dataframes)
                            data.append(row_data)
        disturbance_df = pd.DataFrame(data)
        disturbance_df = self.utils_class._drop_zero_area_rows(disturbance_df)
        return disturbance_df
    
            

