import pandas as pd
import os
import cbm_runner.parser as parser
from cbm_runner.loader import Loader
from cbm_runner.cbm_runner_data_manager import DataManager
    
class Inventory:
    def __init__(self, config_path, afforestation_data):
        self.loader_class = Loader()
        self.data_manager_class = DataManager(config_path)
        self.afforestation_data = afforestation_data
        self.age_df = self.loader_class.forest_age_structure()
        self.classifiers = self.data_manager_class.config_data["Classifiers"]


    def legacy_forest_inventory(self):

        legacy_data = self.loader_class.NIR_forest_data_ha()
        species_proportion = self.data_manager_class.species_proportions

        legacy_year = self.data_manager_class.forest_baseline_year

        species = ["BL", "CF"]

        cols = ["species", "peat", "mineral"]

        data = pd.DataFrame(columns=cols)

        for i, key in enumerate(species):
            data.loc[i, "species"] = key
            data.loc[i, "peat"] = legacy_data.loc[legacy_year, "organic_kha"].item() * species_proportion[key]
            data.loc[i, "mineral"] = legacy_data.loc[legacy_year, "mineral_kha"].item() * species_proportion[key]

        return data
    


    def make_inventory_structure(self,
    scenario, path, ID="False", delay=0, UNFCCCLC=2
    ):
        age_df = self.age_df

        classifiers = self.classifiers

        classifiers_path = os.path.join(path, str(scenario), "classifiers.csv")

        classifiers_df = pd.read_csv(classifiers_path)

        classifiers_df = classifiers_df.loc[(classifiers_df["name"] != "_CLASSIFIER")]

        inventory_classifiers_cols = [
            f"Classifier{x}" for x in classifiers_df["classifier_id"].unique()
        ]
        
        inventory_static_cols = [
            "UsingID",
            "Age",
            "Area",
            "Delay",
            "UNFCCCLC",
            "HistDist",
            "LastDist",
        ]

        inventory_cols = inventory_classifiers_cols + inventory_static_cols

        inventory_df = pd.DataFrame(columns=inventory_cols)

        count = 0

        for species in parser.get_inventory_species(classifiers):

            for typ in parser.get_inventory_type(classifiers, species):
                for soil in parser.get_inventory_soil(classifiers, species):
                    for yc in parser.get_inventory_yield_class(classifiers, species):

                        if typ == "L":

                            for yr in age_df["year"]:
                                inventory_df.loc[count, "Classifier1"] = species
                                inventory_df.loc[count, "Classifier2"] = typ
                                inventory_df.loc[count, "Classifier3"] = soil
                                inventory_df.loc[count, "Classifier4"] = yc
                                inventory_df.loc[count, "Age"] = yr

                                count += 1
                        else:
                            inventory_df.loc[count, "Classifier1"] = species
                            inventory_df.loc[count, "Classifier2"] = typ
                            inventory_df.loc[count, "Classifier3"] = soil
                            inventory_df.loc[count, "Classifier4"] = yc
                            inventory_df.loc[count, "Age"] = 0

                            count += 1

            inventory_df["Area"] = 0
            inventory_df["UsingID"] = ID
            inventory_df["Delay"] = delay

            inventory_df.loc[(inventory_df["Classifier2"] == "L"), "UNFCCCLC"] = 0
            inventory_df.loc[(inventory_df["Classifier2"] == "A"), "UNFCCCLC"] = UNFCCCLC


        return inventory_df
    

    def fill_inventory(self,
        inventory_df,
        forest_type,
        species,
        soil,
        yield_class,
        ageID,
    ):
        classifiers = self.classifiers
        age_df = self.age_df
        data_df = self.legacy_forest_inventory()

        mask = (
            (inventory_df["Classifier1"] == species)
            & (inventory_df["Classifier2"] == forest_type)
            & (inventory_df["Classifier3"] == soil)
            & (inventory_df["Classifier4"] == yield_class)
            & (inventory_df["Age"] == ageID)
        )

        affor_mask = (
            (inventory_df["Classifier1"] == species)
            & (inventory_df["Classifier2"] == "A")
            & (inventory_df["Classifier3"] == soil)
            & (inventory_df["Classifier4"] == yield_class)
        )

        data_mask = data_df["species"] == species

        age_mask = age_df["year"] == ageID

        yield_list = classifiers["yield_class"][species]
        yield_dict = {
            list(yield_list[i].keys())[0]: list(yield_list[i].values())[0]
            for i, _ in enumerate(yield_list)
        }

        if forest_type == "L":

            inventory_df.loc[mask, "Area"] = (
                data_df.loc[data_mask, soil].values
                * yield_dict[yield_class]
                * age_df.loc[age_mask, "aggregate"].values
            )
            inventory_df.loc[mask, "HistDist"] = parser.get_historical_disturbance(
                classifiers, forest_type, species
            )  # classifiers["historical_disturbance"][forest_type][species]
            inventory_df.loc[mask, "LastDist"] = parser.get_historical_disturbance(
                classifiers, forest_type, species
            )

        else:

            inventory_df.loc[affor_mask, "Area"] = 0
            inventory_df.loc[affor_mask, "HistDist"] = parser.get_historical_disturbance(
                classifiers, forest_type, species
            )
            inventory_df.loc[affor_mask, "LastDist"] = parser.get_historical_disturbance(
                classifiers, forest_type, species
            )

        return inventory_df
    

    def inventory_iterator(self, inventory_df):

        classifiers = self.classifiers
        age_df = self.age_df

        for AgeID in age_df["year"]:
            for species in parser.get_inventory_species(classifiers):
                for forest_type in parser.get_inventory_type(classifiers, species):
                    for soil in parser.get_inventory_soil(classifiers, species):
                        for yield_class in parser.get_inventory_yield_class(
                            classifiers, species
                        ):

                            inventory_df = self.fill_inventory(
                                inventory_df,
                                forest_type,
                                species,
                                soil,
                                yield_class,
                                AgeID,
                            )

        return inventory_df
    
    def afforestation_inventory(self, scenario, inventory_df):

        legacy_afforestation_mineral_dict = self.legacy_afforestation_mineral_soils()
        legacy_afforestation_peat_dict = self.legacy_afforestation_peat_soils()

        classifiers = self.classifiers

        scenario_afforestation_data = self.afforestation_data 

        mask = scenario_afforestation_data["scenario"] == scenario

        afforestation_areas = scenario_afforestation_data.copy(deep=True)


        scenario_afforestation_areas = afforestation_areas.loc[mask]

        scenario_areas_dicts = dict(
            zip(
                scenario_afforestation_areas.species,
                scenario_afforestation_areas.total_area,
            )
        )

        areas_dicts = {key: scenario_areas_dicts[key] + legacy_afforestation_mineral_dict[key] for key in scenario_areas_dicts}
        

        for key in areas_dicts.keys():
            for soil in parser.get_inventory_soil(classifiers, key):
                

                yield_list = classifiers["yield_class"][key]
                yield_dict = {
                    list(yield_list[i].keys())[0]: list(yield_list[i].values())[0]
                    for i, _ in enumerate(yield_list)
                }

                for yield_key in yield_dict.keys():
                    
                    inventory_mask = (
                        (inventory_df["Classifier1"] == key)
                        & (inventory_df["Classifier2"] == "A")
                        & (inventory_df["Classifier3"] == soil)
                        & (inventory_df["Classifier4"] == yield_key)
                    )

                    if soil == "peat":
                        try:
                            inventory_df.loc[inventory_mask, "Area"] = (
                                legacy_afforestation_peat_dict[key] * yield_dict[yield_key]
                            )
                        except TypeError:
                            inventory_df.loc[inventory_mask, "Area"] = 0
                    else:
                        try:
                            inventory_df.loc[inventory_mask, "Area"] = (
                                areas_dicts[key] * yield_dict[yield_key]
                            )
                        except TypeError:
                            inventory_df.loc[inventory_mask, "Area"] = 0


        return inventory_df
    

    def legacy_afforestation_mineral_soils(self):

        legacy_afforestation_data = self.loader_class.afforesation_areas_NIR()
        legacy_proportions = self.loader_class.afforesation_species_breakdown()
        legacy_year = self.data_manager_class.forest_baseline_year
        cols =["BL", "CF"]

        afforest_df = pd.DataFrame(columns=cols)

        for year in legacy_afforestation_data.index:
            for col in afforest_df.columns:
                if year >= legacy_year:
                    if col == "BL":
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "mineral_kha"].item() * legacy_proportions.loc[year,"broadleaf"].item()
                    else:
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "mineral_kha"].item() * legacy_proportions.loc[year,"conifer"].item()

        column_sums = afforest_df.sum()

        column_sums_dict = column_sums.to_dict()


        return column_sums_dict
    

    def legacy_afforestation_peat_soils(self):

        legacy_afforestation_data = self.loader_class.afforesation_areas_NIR()
        legacy_proportions = self.loader_class.afforesation_species_breakdown()
        legacy_year = self.data_manager_class.forest_baseline_year
        cols =["BL", "CF"]

        afforest_df = pd.DataFrame(columns=cols)

        for year in legacy_afforestation_data.index:
            for col in afforest_df.columns:
                if year >= legacy_year:
                    if col == "BL":
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "organic_kha"].item() * legacy_proportions.loc[year,"broadleaf"].item()
                    else:
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "organic_kha"].item() * legacy_proportions.loc[year,"conifer"].item()

        column_sums = afforest_df.sum()

        column_sums_dict = column_sums.to_dict()


        return column_sums_dict
    

    def legacy_afforestation_peat_soils_annual(self):

        legacy_afforestation_data = self.loader_class.afforesation_areas_NIR()
        legacy_proportions = self.loader_class.afforesation_species_breakdown()
        legacy_year = self.data_manager_class.forest_baseline_year
        cols =["BL", "CF"]

        afforest_df = pd.DataFrame(columns=cols)

        for year in legacy_afforestation_data.index:
            for col in afforest_df.columns:
                if year >= legacy_year:
                    if col == "BL":
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "organic_kha"].item() * legacy_proportions.loc[year,"broadleaf"].item()
                    else:
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "organic_kha"].item() * legacy_proportions.loc[year,"conifer"].item()


        afforest_dict = afforest_df.to_dict()


        return afforest_dict
    

    def legacy_afforestation_mineral_soils_annual(self):

        legacy_afforestation_data = self.loader_class.afforesation_areas_NIR()
        legacy_proportions = self.loader_class.afforesation_species_breakdown()
        legacy_year = self.data_manager_class.forest_baseline_year
        cols =["BL", "CF"]

        afforest_df = pd.DataFrame(columns=cols)

        for year in legacy_afforestation_data.index:
            for col in afforest_df.columns:
                if year >= legacy_year:
                    if col == "BL":
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "mineral_kha"].item() * legacy_proportions.loc[year,"broadleaf"].item()
                    else:
                        afforest_df.loc[year, col] = legacy_afforestation_data.loc[year, "mineral_kha"].item() * legacy_proportions.loc[year,"conifer"].item()

        afforest_dict = afforest_df.to_dict()


        return afforest_dict