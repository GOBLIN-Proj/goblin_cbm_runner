"""
SC Disturbances Module
======================
This module is responsible for managing disturbances within a CBM (Carbon Budget Modeling) model.

It manages the creation of the disturbance input for land use areas generated as part of scenarios. 
"""
from goblin_cbm_runner.cbm.data_processing.default_processing.disturnance_utils import DisturbUtils
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
from goblin_cbm_runner.resource_manager.loader import Loader
from goblin_cbm_runner.cbm.data_processing.default_processing.SC_inventory import SCInventory
import pandas as pd
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker
import warnings



class SCDisturbances:
    """
    Manages disturbances within a CBM (Carbon Budget Model) model, addressing both legacy and scenario-based disturbances. 
    This class plays a pivotal role in simulating the impact of disturbances on forest carbon stocks and fluxes, 
    adapting to user-defined management strategies and afforestation scenarios.

    Attributes:
        forest_end_year (int): The final year for simulation, defining the temporal boundary for scenario execution.
        calibration_year (int): The initial year for data calibration.
        loader_class (Loader): Instance of Loader for loading data from various sources.
        utils_class (DisturbUtils): Instance of DisturbUtils for managing disturbance data.
        data_manager_class (DataManager): Instance of DataManager for managing simulation data and configurations.
        afforestation_data (DataFrame): Detailed data of afforestation activities per scenario.
        disturbance_timing (DataFrame): Dataframe containing disturbance timing information.
        scenario_disturbance_dict (dict): Dictionary containing scenario disturbance data.

        
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

        self.afforestation_data = afforestation_data

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.scenario_disturbance_dict = self.data_manager_class.get_scenario_disturbance_dict()

    def generic_afforestation_area(self):

        afforest_pre_sc_rate = self.data_manager_class.get_annual_afforestation_rate()

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        for species in parser.get_inventory_species(classifiers):
    
            result_dict[species] = {}

            # Determine the share of the adjustment for species
            species_proportion = self.data_manager_class.get_afforestation_species_distribution(species)
                
            for yield_class in parser.get_species_yield_category(classifiers, species):
                
                yield_proportion = parser.get_yield_class_proportions(classifiers, species, yield_class)
            

                result_dict[species][yield_class] ={}
                result_dict[species][yield_class]["mineral"] = afforest_pre_sc_rate * species_proportion * yield_proportion

        return result_dict

    def scenario_afforestation_area(self, scenario):
        """
        Calculates the afforestation area for a given scenario.

        Parameters:
            scenario (str): The scenario to calculate afforestation for.

        Returns:
            dict: A dictionary with species as keys and afforestation areas as values.
        """
        afforest_delay = self.data_manager_class.get_afforest_delay()
        afforest_pre_sc_rate = self.data_manager_class.get_annual_afforestation_rate()

        area_adjustment = afforest_pre_sc_rate * afforest_delay

        scenario_years = self.forest_end_year - self.calibration_year

        if afforest_delay >= scenario_years:
            raise ValueError(f"Afforestation delay ({afforest_delay} years) is greater than or equal to scenario duration ({scenario_years} years). This scenario is not valid.")

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        aggregated_data = self.afforestation_data.groupby(['species', 'yield_class', 'scenario'])['total_area'].sum().reset_index()

        total_adjustment_applied = 0 

        for species in parser.get_inventory_species(classifiers):

            species_data = aggregated_data[(aggregated_data['species'] == species) & (aggregated_data['scenario'] == scenario)]
    
            result_dict[species] = {}

            # Determine the share of the adjustment for species
            species_proportion = self.data_manager_class.get_afforestation_species_distribution(species)
                
            for index, row in species_data.iterrows():

                yield_class = row['yield_class']
                total_area = row['total_area']
                
                # Adjust the area ensuring it doesn't go below 0
                adjustment_per_yield_class = (area_adjustment * species_proportion) / len(species_data)
                actual_area = max(total_area - adjustment_per_yield_class, 0)
                total_adjustment_applied += (total_area - actual_area)


                if actual_area == 0:
                    warnings.warn(f"Adjusted area for species '{species}' and yield class '{yield_class}' is 0 after adjustment.")


                result_dict[species][yield_class] ={}
                result_dict[species][yield_class]["mineral"] = actual_area / (scenario_years - afforest_delay)


            # Ensure that the total adjustment applied matches the area adjustment
        if abs(total_adjustment_applied - area_adjustment) > 1e-6:
            warnings.warn(f"Total adjustment applied ({total_adjustment_applied}) does not match the intended area adjustment ({area_adjustment}).")
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
        afforest_delay = self.data_manager_class.get_afforest_delay()

        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        #for delay years
        generic_afforestation_inventory = self.generic_afforestation_area()

        disturbance_timing = self.disturbance_timing 

        target_year = self.forest_end_year
        calibration_year = self.calibration_year

        scenario_years = (target_year - calibration_year) + 1

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for yr in range(1, (scenario_years + 1)):
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

                            if yr <= afforest_delay:
                                dataframes = {"afforestation_inventory":generic_afforestation_inventory}
                            else:
                                dataframes = {"afforestation_inventory":afforestation_inventory}

                            self.utils_class._process_scenario_row_data(row_data,context, dataframes)

                            self.utils_class._process_scenario_harvest_data(tracker, row_data, context)

                            data.append(row_data)
            tracker.move_to_next_age()

        for yr in range(1, (scenario_years + 1)):
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


            

