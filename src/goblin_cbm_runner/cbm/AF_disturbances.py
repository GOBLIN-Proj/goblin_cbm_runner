"""
Disturbances Module
===================
This module is responsible for managing disturbances within a CBM (Carbon Budget Modeling) model.
It handles various aspects of disturbances including scenario afforestation areas, legacy disturbance afforestation, 
disturbance structures, and filling data for legacy and scenario-based disturbances.
"""
from goblin_cbm_runner.cbm.disturnance_utils import DisturbUtils
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.inventory import Inventory
import pandas as pd
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class AFDisturbances:
    """
    Manages disturbances within a CBM (Carbon Budget Model) model, addressing both legacy and scenario-based disturbances. 
    This class plays a pivotal role in simulating the impact of disturbances on forest carbon stocks and fluxes, 
    adapting to user-defined management strategies and afforestation scenarios.

    Attributes:
        forest_end_year (int): Target year for simulation end, dictating the temporal scope of forest data.
        calibration_year (int): Base year for data calibration, aligning historical disturbance data with current simulations.
        loader_class (Loader): Facilitates loading and processing external disturbance and afforestation data.
        data_manager_class (DataManager): Manages data configurations, ensuring alignment with user-defined scenarios and CBM configurations.
        baseline_forest_classifiers (dict): Classifies baseline forest scenarios, crucial for distinguishing legacy disturbances.
        scenario_forest_classifiers (dict): Classifies scenario-specific forest data, essential for implementing management strategies.
        afforestation_data (DataFrame): Stores afforestation data, central to calculating scenario-specific afforestation impacts.
        inventory_class (Inventory): Manages forest inventory data, linking afforestation data with forest carbon dynamics.
        disturbance_timing (DataFrame): Schedules the timing of disturbances, integral for temporal dynamics in simulation.
        disturbance_dataframe (DataFrame): Contains detailed records of disturbances, serving as a primary input for simulation processes.
        scenario_disturbance_dict (dict): Maps scenarios to their respective disturbances, enabling tailored management strategies.
        legacy_disturbance_dict (dict): Maintains a record of historical disturbances.
        yield_name_dict (dict): Correlates yield classes with species names.

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

        self.baseline_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Baseline"
        ]
        self.scenario_forest_classifiers = self.data_manager_class.get_classifiers()[
            "Scenario"
        ]
        self.afforestation_data = afforestation_data
        self.inventory_class = Inventory(
            calibration_year, config_path, afforestation_data
        )

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.disturbance_dataframe = self.loader_class.disturbance_data()
        self.scenario_disturbance_dict = self.data_manager_class.get_scenario_disturbance_dict()
        self.legacy_disturbance_dict = self.data_manager_class.get_legacy_disturbance_dict()
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
    


    def get_legacy_forest_area_breakdown(self):
        """
        Calculate the breakdown of legacy forest area based on species, yield class, soil type, and age.

        Returns:
            pandas.DataFrame: DataFrame containing the breakdown of legacy forest area.
        """
        age_df = self.loader_class.forest_age_structure()
        data_df = self.inventory_class.legacy_forest_inventory()
        yield_dict = self.data_manager_class.get_yield_baseline_dict()

        data = []
        for species in data_df["species"].unique():
            for soil in ["mineral", "peat"]:
                for yc in yield_dict[species].keys():
                    for age in age_df["year"].unique():

                        data_mask = data_df["species"] == species
                        age_mask = age_df["year"] == age

                        row_data = {
                            "species": species,
                            "yield_class": yc,
                            "soil": soil,
                            "age": age,
                            "area": data_df.loc[data_mask, soil].item() * yield_dict[species][yc] * age_df.loc[age_mask, "aggregate"].item()
                        }
                        data.append(row_data)

        return pd.DataFrame(data)
    
            

