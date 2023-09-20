import cbm_runner.parser as parser
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.loader import Loader
from cbm_runner.inventory import Inventory
from cbm_runner.harvest import Harvest
import pandas as pd
import itertools
from collections import defaultdict


class Distrubances:
    def __init__(self, config_path, calibration_year, forest_end_year, afforestation_data, scenario_data):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
        self.loader_class = Loader()
        self.data_manager_class = DataManager(config_path, scenario_data)
        self.baseline_forest_classifiers = self.data_manager_class.config_data["Classifiers"]["baseline_forest"]
        self.scenario_forest_classifiers = self.data_manager_class.config_data["Classifiers"]["scenario_forest"]
        self.afforestation_data = afforestation_data
        self.inventory_class = Inventory(config_path, afforestation_data)
        self.harvest_class = Harvest(config_path)

    
    def scenario_afforestation_area(self, scenario):
        
        scenario_years = self.forest_end_year - self.calibration_year

        result_dict = {}

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
        else:
            classifiers = self.baseline_forest_classifiers

        for species in parser.get_inventory_species(classifiers):

            mask = (self.afforestation_data["species"]== species) & (self.afforestation_data["scenario"] == scenario)
            

            result_dict[species] = {}
            result_dict[species]["mineral"] = self.afforestation_data.loc[mask, "total_area"].item()/scenario_years
            
        

        return result_dict


    def legacy_disturbance_afforestation_area(self,scenario, years):
        
        years = list(range(1, years +1))

  
        result_dataframe = pd.DataFrame()


        classifiers = self.scenario_forest_classifiers
        year_index = self.data_manager_class.afforestation_baseline - 1


        afforestation_mineral = self.inventory_class.legacy_afforestation_mineral_soils_annual()
        afforestation_organic = self.inventory_class.legacy_afforestation_peat_soils_annual()

        year_count = 1
        index = 0

        for species in parser.get_inventory_species(classifiers):

            for i in years:

                result_dataframe.at[index, "year"] = year_count
                result_dataframe.at[index, "species"] = species

                try:
                    if year_count == 1:
                        result_dataframe.at[index, "mineral"] = 0
                        result_dataframe.at[index, "peat"] = 0
                    
                    else:

                            result_dataframe.at[index, "mineral"] = afforestation_mineral[species][year_index + year_count] + result_dataframe.at[index -1, "mineral"]
                            result_dataframe.at[index, "peat"] = afforestation_organic[species][year_index + year_count] + result_dataframe.at[index - 1, "peat"]                  
                except KeyError:
                    result_dataframe.at[index, "mineral"] =0
                    result_dataframe.at[index, "peat"] = 0
                index+=1
                year_count +=1

            year_count = 1


        return result_dataframe


    def legacy_disturbance_calculation(self,legacy_value, yield_class, age_ids, disturbance_proprtion
    ):
        age_df = self.loader_class.forest_age_structure()
        classifiers = self.classifiers

        result = 0

        yield_list = parser.get_yield_class(classifiers, "CF")
        yield_dict = {
            list(yield_list[i].keys())[0]: list(yield_list[i].values())[0]
            for i, _ in enumerate(yield_list)
        }

        age = parser.get_age_classifier(classifiers)

        for ID in age_ids:

            age_mask = age_df["year"] == age[ID]

            result += (
                legacy_value
                * yield_dict[yield_class]
                * age_df.loc[age_mask, "aggregate"].values
                * disturbance_proprtion
            )

        return result[0]

    def disturbance_structure(self):
        columns = self.data_manager_class.disturbance_cols
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df
    

    def fill_legacy_data(self, scenario):

        classifiers = self.scenario_forest_classifiers
        disturbances = ["DISTID4"]
        forest_baseline_year = self.data_manager_class.afforestation_baseline


        static_cols = self.data_manager_class.static_disturbance_cols

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()

        legacy_years = calibration_year - forest_baseline_year

        legacy_afforestation_inventory = self.legacy_disturbance_afforestation_area(scenario, legacy_years)

        count = 0
        for yr in range(1, (legacy_years +1)):
            for dist in disturbances:
                for species in parser.get_inventory_species(classifiers):

                    classifier_combo = [
                        *[parser.get_inventory_type(classifiers, species)],
                        *[parser.get_inventory_soil(classifiers, species)],
                        *[parser.get_inventory_yield_class(classifiers, species)]
                    ]

                    combinations = itertools.product(*classifier_combo)

                    for combination in combinations:
                        forest_type, soil, yield_class = combination

                        disturbance_df.at[count, "Classifier1"] = species
                        disturbance_df.at[count, "Classifier2"] = forest_type
                        disturbance_df.at[count, "Classifier3"] = soil
                        disturbance_df.at[count, "Classifier4"] = yield_class

                        disturbance_df.at[count, "UsingID"] = False
                        disturbance_df.at[count, "Year"] = yr
                        disturbance_df.at[count, "DistTypeID"] = dist
                        disturbance_df.at[count, "MeasureType"] = "A"
                        disturbance_df.at[count, "SortType"] = 3
                        disturbance_df.at[count, "Efficiency"] = 1

                        disturbance_df.at[count, "sw_age_min"] = -1
                        disturbance_df.at[count, "sw_age_max"] = -1 
                        disturbance_df.at[count, "hw_age_min"] = -1 
                        disturbance_df.at[count, "hw_age_max"] = -1

                        disturbance_df.loc[count, static_cols] = -1
 
                        if forest_type == "A":
                            mask = ((legacy_afforestation_inventory["species"] == species) & (legacy_afforestation_inventory["year"] == yr))
                            
                            if disturbance_df.loc[count, "Classifier3"] == "mineral":

                                disturbance_df.loc[count, "Amount"] = (legacy_afforestation_inventory.loc[
                                        mask, "mineral"
                                    ].item()
                                    * parser.get_yield_class_proportions(classifiers, species, yield_class))
                            else:
                                disturbance_df.loc[count, "Amount"] = (legacy_afforestation_inventory.loc[
                                        mask, "peat"
                                    ].item()
                                    * parser.get_yield_class_proportions(classifiers, species, yield_class))
                                
                        else:
                            disturbance_df.loc[count, "Amount"] = 0

                        count += 1


        zero_area_mask = disturbance_df["Amount"] == 0
        disturbance_df.drop(disturbance_df.loc[zero_area_mask].index, inplace=True)
        
        return disturbance_df
    

    def fill_baseline_forest(self):

        forest_baseline_year = self.data_manager_class.forest_baseline_year
        classifiers = self.baseline_forest_classifiers
        disturbances = ["DISTID1", "DISTID2"]

        static_cols = self.data_manager_class.static_disturbance_cols

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()

        legacy_years = calibration_year - forest_baseline_year

        disturbance_age_dict = self.data_manager_class.disturbance_age_dict

        harvest_df = self.harvest_class.get_harvest_areas()

        count = 0
        for yr in range(1, (legacy_years +1)):
            for dist in disturbances:
                for species in parser.get_inventory_species(classifiers):

                    classifier_combo = [
                        *[parser.get_inventory_type(classifiers, species)],
                        *[parser.get_inventory_soil(classifiers, species)],
                        *[parser.get_inventory_yield_class(classifiers, species)]
                    ]

                    combinations = itertools.product(*classifier_combo)

                    for combination in combinations:
                        forest_type, soil, yield_class = combination

                        disturbance_df.at[count, "Classifier1"] = species
                        disturbance_df.at[count, "Classifier2"] = forest_type
                        disturbance_df.at[count, "Classifier3"] = soil
                        disturbance_df.at[count, "Classifier4"] = yield_class

                        disturbance_df.at[count, "UsingID"] = False
                        disturbance_df.at[count, "Year"] = yr
                        disturbance_df.at[count, "DistTypeID"] = dist
                        disturbance_df.at[count, "MeasureType"] = "A"
                        disturbance_df.at[count, "SortType"] = 3
                        disturbance_df.at[count, "Efficiency"] = 1

                        disturbance_df.at[count, "sw_age_min"] = disturbance_age_dict[dist][species][yield_class]["sw_age_min"]
                        disturbance_df.at[count, "sw_age_max"] = disturbance_age_dict[dist][species][yield_class]["sw_age_max"]
                        disturbance_df.at[count, "hw_age_min"] = disturbance_age_dict[dist][species][yield_class]["hw_age_min"]
                        disturbance_df.at[count, "hw_age_max"] = disturbance_age_dict[dist][species][yield_class]["hw_age_max"]

                        disturbance_df.loc[count, static_cols] = -1

                        if species == "CF" and dist == "DISTID1":
                            harvest_year = yr + forest_baseline_year
                            legacy_mask = ((harvest_df["yield_class"] == yield_class) & (harvest_df["year"] == harvest_year))
                
                            if not harvest_df[legacy_mask].empty:
                                    disturbance_df.loc[count, "Amount"] = harvest_df.loc[legacy_mask, soil].item()
                            else: 
                                disturbance_df.loc[count, "Amount"] = 0
                        else:
                            disturbance_df.loc[count, "Amount"] = 0

                        count += 1

        zero_area_mask = disturbance_df["Amount"] == 0
        disturbance_df.drop(disturbance_df.loc[zero_area_mask].index, inplace=True)                
        
        return disturbance_df


    def fill_scenario_data(self, scenario):

        classifiers = self.scenario_forest_classifiers
        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_df = self.fill_legacy_data(scenario)

        legacy_end_year = disturbance_df.Year.max()

        static_cols = self.data_manager_class.static_disturbance_cols

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(range(legacy_end_year, scenario_years +1))

        disturbance_age_dict = self.data_manager_class.disturbance_age_dict
        

        disturbances = ["DISTID4"]

        count = disturbance_df.index.max()

        for yr in years:      
            for dist in disturbances:
                for species in parser.get_inventory_species(classifiers):

                    classifier_combo = [
                        *[parser.get_inventory_type(classifiers, species)],
                        *[parser.get_inventory_soil(classifiers, species)],
                        *[parser.get_inventory_yield_class(classifiers, species)]
                    ]

                    combinations = itertools.product(*classifier_combo)

                    for combination in combinations:
                        forest_type, soil, yield_class = combination

                        disturbance_df.at[count, "Classifier1"] = species
                        disturbance_df.at[count, "Classifier2"] = forest_type
                        disturbance_df.at[count, "Classifier3"] = soil
                        disturbance_df.at[count, "Classifier4"] = yield_class

                        disturbance_df.at[count, "UsingID"] = True
                        disturbance_df.at[count, "Year"] = yr
                        disturbance_df.at[count, "DistTypeID"] = dist
                        disturbance_df.at[count, "MeasureType"] = "A"
                        disturbance_df.at[count, "SortType"] = 3
                        disturbance_df.at[count, "Efficiency"] = 1

                        disturbance_df.at[count, "sw_age_min"] = -1
                        disturbance_df.at[count, "sw_age_max"] = -1
                        disturbance_df.at[count, "hw_age_min"] = -1
                        disturbance_df.at[count, "hw_age_max"] = -1

                        disturbance_df.loc[count, static_cols] = -1

                        if forest_type == "A":
                                
                                afforestation_value = afforestation_inventory[species]["mineral"] 
                                
                                if disturbance_df.loc[count, "Classifier3"] == "mineral":

                                    disturbance_df.loc[count, "Amount"] = (afforestation_value
                                        * parser.get_yield_class_proportions(classifiers, species, yield_class))
            
                                    
                                else:
                                    disturbance_df.loc[count, "Amount"] = 0
                        else:
                            disturbance_df.loc[count, "Amount"] = 0

                                
                        count += 1


        zero_area_mask = disturbance_df["Amount"] == 0
        disturbance_df.drop(disturbance_df.loc[zero_area_mask].index, inplace=True)
        
        return disturbance_df