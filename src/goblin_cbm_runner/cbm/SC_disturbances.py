"""
Disturbances Module
===================
This module is responsible for managing disturbances within a CBM (Carbon Budget Modeling) model.
It handles various aspects of disturbances including scenario afforestation areas, legacy disturbance afforestation, 
disturbance structures, and filling data for legacy and scenario-based disturbances.
"""
from goblin_cbm_runner.cbm.disturnance_utils import DisturbUtils
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.inventory import Inventory
import pandas as pd
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class SCDisturbances:
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

        self.utils_class = DisturbUtils(
            config_path, calibration_year,forest_end_year, scenario_data
        )
        self.data_manager_class = DataManager(
            calibration_year=calibration_year, config_file=config_path, scenario_data=scenario_data
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


    def scenario_afforestation_area(self, scenario):
        """
        Calculates the afforestation area for a given scenario.

        Parameters:
            scenario (str): The scenario to calculate afforestation for.

        Returns:
            dict: A dictionary with species as keys and afforestation areas as values.
        """
        scenario_years = self.forest_end_year - self.calibration_year

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        aggregated_data = self.afforestation_data.groupby(['species', 'yield_class', 'scenario'])['total_area'].sum().reset_index()

        for species in parser.get_inventory_species(classifiers):

            species_data = aggregated_data[(aggregated_data['species'] == species) & (aggregated_data['scenario'] == scenario)]
    
            result_dict[species] = {}
                
            for index, row in species_data.iterrows():

                yield_class = row['yield_class']
                total_area = row['total_area']
                
                result_dict[species][yield_class] ={}
                result_dict[species][yield_class]["mineral"] = total_area / scenario_years

        return result_dict


    def fill_scenario_data(self, scenario):
        """
        Fills the disturbance data for a given scenario. The final dataframe will include the data from legacy afforestation (afforestation from 1990)
        as well as user defined scenario data.

        Args:
            scenario: The scenario for which to fill the disturbance data.

        Returns:
            The disturbance data DataFrame after filling with scenario data.
        """
        
        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_timing = self.disturbance_timing 

        target_year = self.forest_end_year
        calibration_year = self.calibration_year

        scenario_years = (target_year - calibration_year) + 1

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for yr in range(0, (scenario_years + 1)):
            for dist in disturbances:
                if dist == "DISTID4":
                    for species in parser.get_inventory_species(configuration_classifiers):
                        combinations = self.utils_class._get_scenario_classifier_combinations()

                        for combination in combinations:
                            forest_type, soil, yield_class = combination

                            row_data = self.utils_class._generate_row(species, forest_type, soil, yield_class, dist, yr)

                            context = {"forest_type":forest_type, 
                                        "species":species, 
                                        "soil":soil, 
                                        "yield_class":yield_class, 
                                        "dist":dist, 
                                        "year":yr,
                                        "configuration_classifiers":configuration_classifiers,
                                        "non_forest_dict":non_forest_dict,
                                        "harvest_proportion": self.scenario_disturbance_dict[scenario][species],
                                        "age": 0
                                }

                            dataframes = {"afforestation_inventory":afforestation_inventory}

                            self.utils_class._process_scenario_row_data(row_data,context, dataframes)

                            self.utils_class._process_scenario_harvest_data(tracker, row_data, context)

                            data.append(row_data)
            tracker.move_to_next_age()

        for yr in range(0, (scenario_years + 1)):
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

        scenario_disturbance_df = pd.DataFrame(data)

        disturbance_df = self.utils_class._drop_zero_area_rows(scenario_disturbance_df)


        return disturbance_df


            

