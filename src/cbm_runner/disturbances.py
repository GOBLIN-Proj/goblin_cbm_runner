import cbm_runner.parser as parser
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.loader import Loader
from cbm_runner.inventory import Inventory
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

        year_index = self.data_manager_class.forest_baseline_year - 1
  
        result_dataframe = pd.DataFrame()

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
        else:
            classifiers = self.baseline_forest_classifiers

        afforestation_mineral = self.inventory_class.legacy_afforestation_mineral_soils_annual()
        afforestation_organic = self.inventory_class.legacy_afforestation_peat_soils_annual()

        year_count = 1
        index = 0

        for species in parser.get_inventory_species(classifiers):

            for i in years:

                result_dataframe.at[index, "year"] = year_count
                result_dataframe.at[index, "species"] = species

                if year_count == 1:
                    result_dataframe.at[index, "mineral"] = 0
                    result_dataframe.at[index, "peat"] = 0

                else:

                    result_dataframe.at[index, "mineral"] = afforestation_mineral[species][year_index + year_count] + result_dataframe.at[index -1, "mineral"]
                    result_dataframe.at[index, "peat"] = afforestation_organic[species][year_index + year_count] + result_dataframe.at[index - 1, "peat"]                  

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

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
        else:
            classifiers = self.baseline_forest_classifiers

        static_cols = self.data_manager_class.static_disturbance_cols

        calibration_year = self.calibration_year
        forest_baseline_year = self.data_manager_class.forest_baseline_year

        disturbance_df = self.disturbance_structure()

        legacy_years = calibration_year - forest_baseline_year

        disturbance_dict = self.data_manager_class.disturbance_dict
        disturbance_age_dict = self.data_manager_class.disturbance_age_dict

        legacy_afforestation_inventory = self.legacy_disturbance_afforestation_area(scenario, legacy_years)
        legacy_inventory = self.inventory_class.legacy_forest_inventory()

        disturbances = ["DISTID1", "DISTID2", "DISTID4"]

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

                        disturbance_df.at[count, "UsingID"] = True
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

    
 
                        if dist != "DISTID4":

                            if forest_type == "L":
                           
                                mask = ((legacy_afforestation_inventory["species"] == species) & (legacy_afforestation_inventory["year"] == yr))
                                legacy_mask = ((legacy_inventory["species"] == species))

                                try:
                                    disturbance_df.loc[count, "Amount"] = (
                                        legacy_afforestation_inventory.loc[
                                            mask, "mineral"
                                        ].item()
                                        * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                        * disturbance_dict[dist][species]()()
                                    ) + (
                                        legacy_inventory.loc[
                                            legacy_mask, "mineral"
                                        ].item()
                                        * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                        * disturbance_dict[dist][species]()()

                                    )

                                except TypeError:
                                        disturbance_df.loc[count, "Amount"] = (
                                        legacy_afforestation_inventory.loc[
                                            mask, "mineral"
                                        ].item()
                                        * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                        * disturbance_dict[dist][species]
                                            ) + (
                                        legacy_inventory.loc[
                                            legacy_mask, "mineral"
                                        ].item()
                                        * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                        * disturbance_dict[dist][species]
                                            )
                            else: 
                                
                                disturbance_df.loc[count, "Amount"] = 0
                        else:

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


    def fill_scenario_data(self, scenario):

        disturbance_df = self.fill_legacy_data(scenario)


        legacy_end_year = disturbance_df.Year.max()

        if scenario is not None:
            classifiers = self.scenario_forest_classifiers
            afforestation_inventory = self.scenario_afforestation_area(scenario)
        else:
            classifiers = self.baseline_forest_classifiers
            afforestation_inventory = 0

        static_cols = self.data_manager_class.static_disturbance_cols

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(range(legacy_end_year, scenario_years +1))

        if scenario is None or scenario < 0:
            disturbance_dict = self.data_manager_class.disturbance_dict
        else:
            disturbance_dict = self.data_manager_class.scenario_disturbance_dict[scenario]

        disturbance_age_dict = self.data_manager_class.disturbance_age_dict
        

        disturbances = ["DISTID1", "DISTID2", "DISTID4"]

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

                        disturbance_df.at[count, "sw_age_min"] = disturbance_age_dict[dist][species][yield_class]["sw_age_min"]
                        disturbance_df.at[count, "sw_age_max"] = disturbance_age_dict[dist][species][yield_class]["sw_age_max"]
                        disturbance_df.at[count, "hw_age_min"] = disturbance_age_dict[dist][species][yield_class]["hw_age_min"]
                        disturbance_df.at[count, "hw_age_max"] = disturbance_age_dict[dist][species][yield_class]["hw_age_max"]

                        disturbance_df.loc[count, static_cols] = -1


                        if dist != "DISTID4":

                            if forest_type == "L":
                                
                                if afforestation_inventory != 0:
                                    afforestation_value = afforestation_inventory[species]["mineral"] * ( yr - legacy_end_year)
                                else:
                                    afforestation_value = 0

                                legacy_mask = ((disturbance_df["Year"] == legacy_end_year-1) & (disturbance_df["Classifier1"]== species) & (disturbance_df["Classifier2"]=="L") & (disturbance_df["Classifier3"]== soil) & (disturbance_df["Classifier4"]==yield_class) & (disturbance_df["DistTypeID"]== dist))
                                try:
                                    legacy_value = disturbance_df.loc[legacy_mask, "Amount"].unique().item()
                                except ValueError:
                                    legacy_value = 0 

                                if soil == "mineral":

                                    try: 
                                        afforest_value = (afforestation_value
                                                * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                                * disturbance_dict[dist][species]()())
                                    except TypeError:
                                        afforest_value = (afforestation_value
                                                * parser.get_yield_class_proportions(classifiers, species, yield_class)
                                                * disturbance_dict[dist][species])
                                        
                                    disturbance_df.loc[count, "Amount"] = afforest_value + legacy_value
                                        

                                else: 
                                    disturbance_df.loc[count, "Amount"] = legacy_value


                            else: 
                                
                                disturbance_df.loc[count, "Amount"] = 0
                        else:
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