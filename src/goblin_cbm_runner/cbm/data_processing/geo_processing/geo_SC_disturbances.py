"""
Geo Disturbances Module
=======================
This module manages disturbances within the Carbon Budget Modeling (CBM) framework, specifically tailored for scenarios
involving afforestation areas at the catchment level, both legacy and scenario-specific disturbances. It organizes and processes
disturbance data to support the simulation of forest dynamics under varying management and disturbance scenarios.

"""
import goblin_cbm_runner.resource_manager.parser as parser
from goblin_cbm_runner.resource_manager.geo_cbm_runner_data_manager import GeoDataManager
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
        config_path (str): Path to the configuration file guiding the simulation setup.
        calibration_year (int): Reference year from which simulation data is calibrated.
        forest_end_year (int): Designated end year for the simulation's forest data.
        afforestation_data (DataFrame): Data detailing afforestation projects, including species and area.
        scenario_data (DataFrame): Data defining various simulation scenarios.

    Methods:

        scenario_afforestation_area(scenario):
            Calculates the afforestation area for a given scenario.

        fill_scenario_data(scenario):
            Fills the disturbance data for a given scenario.

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

        self.afforestation_data = afforestation_data
        self.inventory_class = Inventory(
            calibration_year, config_path, scenario_data, afforestation_data
        )

        self.disturbance_timing = self.loader_class.disturbance_time()
        self.scenario_disturbance_dict = self.data_manager_class.get_scenario_disturbance_dict()



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
        Fills the disturbance data for a given scenario.

        Args:
            scenario: The scenario for which to fill the disturbance data.

        Returns:
            The disturbance data DataFrame after filling with scenario data.
        """
        
        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_timing = self.disturbance_timing 

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(
            range(1, (scenario_years + 1))
        )

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for yr in years:
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

        scenario_disturbance_df = pd.DataFrame(data)

        scenario_disturbance_df = self.utils_class._drop_zero_area_rows(scenario_disturbance_df)

        return scenario_disturbance_df
