"""
Geo Disturbances Module
=======================
This module manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios
involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes
disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

"""
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_inventory import Inventory
from goblin_cbm_runner.cbm.data_processing.geo_processing.geo_disturbance_utils import GeoDisturbUtils
import pandas as pd
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker



class SCDisturbances:
    """
    Manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios 
    involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes 
    disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

    Attributes:
        forest_end_year (int): Target end year for forest simulation data.
        calibration_year (int): Base year for data calibration within the simulation.
        loader_class (Loader): Instance responsible for loading external data resources.
        data_manager_class (DataManager): Manages retrieval and organization of simulation data.
        utils_class (GeoDisturbUtils): Utility class for processing disturbance data.
        afforestation_data (DataFrame): Contains data on afforestation activities, including species and areas.
        inventory_class (Inventory): Manages the preparation and structuring of forest inventory data.
        disturbance_timing (DataFrame): Contains information on the timing and type of disturbances.
        scenario_disturbance_dict (dict): Holds scenario-specific disturbance information.

    Parameters:
        geo_data_manager (GeoDataManager): Manager for geographical data.
    
    Methods:
        scenario_afforestation_area(scenario):
            Calculates the afforestation area for a given scenario.

        gen_afforestation_scenario_disturbances(scenario):
            Generates afforestation scenario disturbances.

        gen_non_afforestation_scenario_disturbances(scenario, afforest_df):
            Generates non-afforestation scenario disturbances.

        fill_scenario_forest(scenario):
            Fills the forest data for a given scenario.
    """
    
    def __init__(self,geo_data_manager,):

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


    def scenario_afforestation_area(self, scenario):
        """
        Calculates the afforestation area for a given scenario.

        Parameters:
            scenario (Scenario): The scenario to calculate afforestation for.

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


    def gen_afforestation_scenario_disturbances(self, scenario):
        """
        Generates afforestation scenario disturbances.

        Args:
            scenario (Scenario): The scenario for which to generate the disturbance data.

        Returns:
            DataFrame: The disturbance data after filling with scenario data.
        """

        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        scenario_years = self.forest_end_year - self.calibration_year

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        afforestation_disturbance = "DISTID4"

        species_classifiers = {
            species: list(self.utils_class._get_scenario_classifier_combinations(species))  # Convert to list
            for species in parser.get_inventory_species(configuration_classifiers)
        }

        data = []

        for yr in range(1, (scenario_years + 1)):
            for species, combinations in species_classifiers.items():           
                for combination in combinations:
                    forest_type, soil, yield_class = combination
                    context = {"forest_type":forest_type, 
                                "species":species, 
                                "soil":soil, 
                                "yield_class":yield_class, 
                                "dist":afforestation_disturbance, 
                                "year":yr,
                                "configuration_classifiers":configuration_classifiers,
                                "non_forest_dict":non_forest_dict,
                                "harvest_proportion":self.scenario_disturbance_dict[scenario][species],
                                "age": 0
                        }
                    

                    row_data = self.utils_class._generate_row(species, forest_type, soil, yield_class, afforestation_disturbance, yr)
            
                    dataframes = {"afforestation_inventory":afforestation_inventory}

                    self.utils_class._process_scenario_row_data(row_data,context, dataframes)

                    
                    data.append(row_data)

        return pd.DataFrame(data)


    
    def gen_non_afforestation_scenario_disturbances(self, scenario, afforest_df):
        """
        Generates non-afforestation scenario disturbances.

        Args:
            scenario (Scenario): The scenario for which to generate the disturbance data.
            afforest_df (DataFrame): DataFrame containing afforestation disturbances.

        Returns:
            DataFrame: The disturbance data after filling with non-afforestation scenario data.
        """
        full_rotation_scenario_years = (self.forest_end_year - self.calibration_year) + 1
        disturdance_dict= self.scenario_disturbance_dict[scenario]

        dist_tracker = AfforestationTracker(self.data_manager_class, disturdance_dict, afforest_df, full_rotation_scenario_years)

        scenario_disturbance_df = dist_tracker.run_simulation()

        disturbance_timing = self.loader_class.disturbance_time()
       
        disturbance_df = self.utils_class.format_disturbance_data(scenario_disturbance_df, disturbance_timing)

        return disturbance_df
    
    
    def fill_scenario_forest(self, scenario):
        """
        Fills the forest data for a given scenario.

        Args:
            scenario (Scenario): The scenario for which to fill the forest data.

        Returns:
            DataFrame: The combined DataFrame of afforestation and non-afforestation disturbances.
        """
        afforestation_scenario_disturbances = self.gen_afforestation_scenario_disturbances(scenario)
        
        non_afforestation_scenario_disturbances = self.gen_non_afforestation_scenario_disturbances(scenario, afforestation_scenario_disturbances)
        
        return pd.concat([afforestation_scenario_disturbances, non_afforestation_scenario_disturbances])