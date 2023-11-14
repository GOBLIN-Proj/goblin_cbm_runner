import cbm_runner.parser as parser
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.loader import Loader
from cbm_runner.inventory import Inventory
import pandas as pd
import itertools
from cbm_runner.harvest import AfforestationTracker
import json


class Distrubances:
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforestation_data,
        scenario_data,
    ):
        self.forest_end_year = forest_end_year
        self.calibration_year = calibration_year
        self.loader_class = Loader()
        self.data_manager_class = DataManager(
            calibration_year, config_path, scenario_data
        )
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
        self.scenario_disturbance_dict = self.data_manager_class.scenario_disturbance_dict
        self.legacy_disturbance_dict = self.data_manager_class.get_legacy_disturbance_dict()


    def scenario_afforestation_area(self, scenario):
        scenario_years = self.forest_end_year - self.calibration_year

        result_dict = {}

        classifiers = self.data_manager_class.config_data

        for species in parser.get_inventory_species(classifiers):
            mask = (self.afforestation_data["species"] == species) & (
                self.afforestation_data["scenario"] == scenario
            )

            result_dict[species] = {}
            result_dict[species]["mineral"] = (
                self.afforestation_data.loc[mask, "total_area"].item() / scenario_years
            )

        return result_dict

    def legacy_disturbance_afforestation_area(self, years):
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


        yield_dict = self.data_manager_class.get_yield_basline_dict()

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


    def disturbance_structure(self):
        columns = self.data_manager_class.get_disturbance_cols()
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df

    def fill_legacy_data(self):

        disturbances = self.data_manager_class.get_disturbances_config()["Scenario"]

        forest_baseline_year = self.data_manager_class.get_afforestation_baseline()

        yield_name_dict = self.data_manager_class.get_yield_name_dict()

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()

        legacy_years = (calibration_year - forest_baseline_year) +1

        legacy_afforestation_inventory = self.legacy_disturbance_afforestation_area(legacy_years)
        disturbance_dataframe = self.disturbance_dataframe

        disturbance_timing = self.disturbance_timing

        data = []

        for yr in range(0, (legacy_years + 1)):
            for dist in disturbances:
                for species in yield_name_dict.keys():
                    classifier_combo = self._get_classifier_combinations()

                    for combination in classifier_combo:
                        forest_type, soil, yield_class = combination

                        row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr+1)

                        context = {"forest_type":forest_type, 
                                   "species":species, 
                                   "soil":soil, 
                                   "yield_class":yield_class, 
                                   "dist":dist, 
                                   "year":yr,
                                    "forest_baseline_year":forest_baseline_year,
                        }

                        dataframes = {"legacy_afforestation_inventory":legacy_afforestation_inventory,
                                        "disturbance_dataframe":disturbance_dataframe,
                                        "disturbance_timing":disturbance_timing,
                            }

                        self._process_row_data(row_data,context, dataframes)
                        
                        data.append(row_data)


        disturbance_df = pd.DataFrame(data)
        disturbance_df = self._drop_zero_area_rows(disturbance_df)

        return disturbance_df
    

    def fill_baseline_forest(self):
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()
        classifiers = self.baseline_forest_classifiers
        disturbance_dataframe = self.disturbance_dataframe
        disturbances = ["DISTID1", "DISTID2"]

        calibration_year = self.calibration_year

        disturbance_df = self.disturbance_structure()

        legacy_years = calibration_year - forest_baseline_year

        disturbance_timing = self.disturbance_timing 

        species_keys = list(classifiers["Species"].keys())

        data = []
        for yr in range(0, (legacy_years + 1)):
            for dist in disturbances:
                for species in species_keys:
                    classifier_combo = self._get_legacy_classifier_combinations()
                    for combination in classifier_combo:
                        forest_type, soil, yield_class = combination

                    row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr+1)
                    
                    context = {"forest_type":forest_type, 
                                   "species":species, 
                                   "soil":soil, 
                                   "yield_class":yield_class, 
                                   "dist":dist, 
                                   "year":yr,
                                    "forest_baseline_year":forest_baseline_year,
                        }

                    dataframes = {"disturbance_dataframe":disturbance_dataframe,
                        "disturbance_timing":disturbance_timing}

                    self._process_row_data(row_data,context, dataframes)
                    
                    #force row to 0 
                    row_data["Amount"] = 0

                    data.append(row_data)

        disturbance_df = pd.DataFrame(data)
        disturbance_df = self._drop_zero_area_rows(disturbance_df)

        return disturbance_df


    def fill_scenario_data(self, scenario):

        configuration_classifiers = self.data_manager_class.config_data

        afforestation_inventory = self.scenario_afforestation_area(scenario)

        disturbance_timing = self.disturbance_timing 

        disturbance_df = self.fill_legacy_data()

        legacy_end_year = disturbance_df.Year.max()

        scenario_years = self.forest_end_year - self.calibration_year
        years = list(
            range((legacy_end_year + 1), (legacy_end_year + (scenario_years + 1)))
        )

        non_forest_dict = self.data_manager_class.get_non_forest_dict()

        disturbances = ["DISTID4", "DISTID1", "DISTID2"]

        tracker = AfforestationTracker()

        data = []

        for yr in years:
            for dist in disturbances:
                if dist == "DISTID4":
                    for species in parser.get_inventory_species(configuration_classifiers):
                        combinations = self._get_scenario_classifier_combinations()

                        for combination in combinations:
                            forest_type, soil, yield_class = combination

                            row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr)

                            context = {"forest_type":forest_type, 
                                        "species":species, 
                                        "soil":soil, 
                                        "yield_class":yield_class, 
                                        "dist":dist, 
                                        "year":yr,
                                        "configuration_classifiers":configuration_classifiers,
                                        "non_forest_dict":non_forest_dict,
                                        "harvest_proportion": self.scenario_disturbance_dict[scenario][species],
                                }

                            dataframes = {"afforestation_inventory":afforestation_inventory}

                            self._process_scenario_row_data(row_data,context, dataframes)

                            self._process_scenario_harvest_data(tracker, row_data, context)

                            data.append(row_data)
            tracker.move_to_next_age()

        for yr in years:
            for stand in tracker.disturbed_stands:
                if stand.year == yr:
                    
                    row_data = self._generate_row(stand.species, "L", stand.soil, stand.yield_class, stand.dist, yr)

                    context = {"forest_type":"L",
                                "species":stand.species,
                                "yield_class":stand.yield_class,
                                "area":stand.area,
                                "dist":stand.dist,}
                    dataframes = {"disturbance_timing":disturbance_timing}

                    self._process_scenario_row_data(row_data,context, dataframes)

                    data.append(row_data)

        scenario_disturbance_df = pd.DataFrame(data)
        disturbance_df = pd.concat(
            [disturbance_df, scenario_disturbance_df], axis=0, ignore_index=True
        )
        disturbance_df = self._drop_zero_area_rows(disturbance_df)

        return disturbance_df


    def _process_scenario_harvest_data(self, tracker, row_data, context):
        dist = context["dist"]
        area = row_data["Amount"]
        if dist == "DISTID4" and area != 0:
            self._track_scenario_harvest(tracker, row_data, context)


    def _track_scenario_harvest(self, tracker, row_data, context):
        
        area = row_data["Amount"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        time = context["year"]
        factor = context["harvest_proportion"]
        
        tracker.afforest(area, species, yield_class, soil)
        tracker.forest_disturbance(time, species, yield_class, soil, factor)


    def _drop_zero_area_rows(self, disturbance_df):
        disturbance_df = disturbance_df[disturbance_df["Amount"] != 0]
        disturbance_df = disturbance_df.reset_index(drop=True)

        disturbance_df = disturbance_df.sort_values(by=["Year"], ascending=True)

        return disturbance_df

    def _get_legacy_classifier_combinations(self):
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["L"]
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)
    
    def _get_scenario_classifier_combinations(self):
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["A"]
        soil_keys = ["mineral"]
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)

    def _get_classifier_combinations(self):
        classifiers = self.scenario_forest_classifiers
        forest_keys = list(classifiers["Forest type"].keys())
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_static_defaults(self):
        static_cols = self.data_manager_class.get_static_disturbance_cols()
        return {col: -1 for col in static_cols}

    def _generate_row(self, species, forest_type, soil, yield_class, dist, yr):
        static_defaults = self._get_static_defaults()
        row_data = {
                    "Classifier1": species,
                    "Classifier2": forest_type,
                    "Classifier3": soil,
                    "Classifier4": yield_class,
                    "UsingID": False,
                    "sw_age_min": 0,
                    "sw_age_max": 210,
                    "hw_age_min": 0,
                    "hw_age_max": 210,
                    "MinYearsSinceDist": -1,
                    **static_defaults,
                    "Efficiency": 1,
                    "SortType": 3,
                    "MeasureType": "A",
                    "Amount": 0,
                    "DistTypeID": dist,
                    "Year": yr,
                        }
        return row_data
    
    def _process_scenario_row_data(self, row_data, context, dataframes):
        forest_type = context["forest_type"]
        dist = context["dist"]

        if forest_type == "A" and dist == "DISTID4":
            self._handle_scenario_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_scenario_forest(row_data, context, dataframes)


    def _process_row_data(self, row_data, context, dataframes):
        forest_type = context["forest_type"]
        dist = context["dist"]

        if forest_type == "A" and dist == "DISTID4":
            self._handle_legacy_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_forest(row_data, context, dataframes)


    def _handle_legacy_scenario_forest(self, row_data, context, dataframes):
        
        if context["dist"] == "DISTID4":
            row_data["Amount"] = 0
        else:
            self._update_disturbance_timing(row_data, context, dataframes)
            area = context["area"]

            row_data["Amount"] = area


    def _handle_scenario_afforestation(self, row_data, context, dataframes):

        afforestation_inventory = dataframes["afforestation_inventory"]
        non_forest_dict = context["non_forest_dict"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        configuration_classifiers = context["configuration_classifiers"]

        row_data["Classifier1"] = non_forest_dict[species][soil]
        afforestation_value = afforestation_inventory[species][
                                soil
                            ]

        if row_data["Classifier3"] == soil:
            try:
                row_data["Amount"] = (
                    afforestation_value
                    * parser.get_yield_class_proportions(
                        configuration_classifiers,
                        species,
                        yield_class,
                    )
                )
            except TypeError:
                row_data["Amount"] = 0

        else:
            row_data["Amount"] = 0



    def _handle_legacy_afforestation(self, row_data, context, dataframes):

        non_forest_dict = self.data_manager_class.get_non_forest_dict()
        legacy_afforestation_inventory = dataframes["legacy_afforestation_inventory"]
        species = context["species"]
        yield_class = context["yield_class"]
        yr = context["year"]
        soil = context["soil"]

        
        mask = (
                    (legacy_afforestation_inventory["species"] == species)
                    & (
                        legacy_afforestation_inventory["yield_class"]
                        == yield_class
                    )
                    & (legacy_afforestation_inventory["year"] == yr)
                    & (legacy_afforestation_inventory["soil"] == soil)
                )
        row_data["Classifier1"] = non_forest_dict[species][soil]
        try:
            row_data["Amount"] = legacy_afforestation_inventory.loc[
                mask, "area_ha"
            ].item()

            #tracker.afforest(row_data["Amount"], species, yield_class)
            #tracker.move_to_next_age()

        except ValueError:
                
            row_data["Amount"] = 0
      


    def _handle_legacy_forest(self, row_data, context, dataframes):
        # ... logic for legacy forest ...
        # This includes your logic for DISTID3, DISTID1, DISTID2, and the else block

        dist = context["dist"]
        disturbance_dataframe = dataframes["disturbance_dataframe"]
        species = context["species"]
        yield_class = context["yield_class"]
        yr = context["year"]
        forest_baseline_year = context["forest_baseline_year"]


        self._update_disturbance_timing(row_data, context, dataframes)

        if dist == "DISTID3":
            mask = (
                (disturbance_dataframe["Species"] == "?")
                & (disturbance_dataframe["Yield_class"] == "?")
                & (
                    disturbance_dataframe["Year"]
                    == (forest_baseline_year + yr)
                )
                & (disturbance_dataframe["Disturbance_id"] == dist)
            )

            try:
                row_data["Amount"] = disturbance_dataframe.loc[
                    mask, "Amount"
                ].item()
                row_data["MeasureType"] = disturbance_dataframe.loc[
                    mask, "M_type"
                ].item()

            except ValueError:
                row_data["Amount"] = 0


        elif (
                dist == "DISTID1" or dist == "DISTID2"
            ):
            mask = (
                    (disturbance_dataframe["Species"] == species)
                    & (disturbance_dataframe["Yield_class"] == yield_class)
                    & (
                        disturbance_dataframe["Year"]
                        == (forest_baseline_year + yr)
                    )
                    & (disturbance_dataframe["Disturbance_id"] == dist)
                )
            row_data["Classifier1"] = species
            try:
                row_data["Amount"] = disturbance_dataframe.loc[
                    mask, "Amount"
                ].item()
                row_data["MeasureType"] = disturbance_dataframe.loc[
                    mask, "M_type"
                ].item()

            except ValueError:
                row_data["Amount"] = 0

        else:
            row_data["Classifier1"] = species
            row_data["Amount"] = 0

    
    def _update_disturbance_timing(self, row_data, context, dataframes):
        """Retrieve disturbance timing information from the disturbance_timing DataFrame."""

        yield_name = self.data_manager_class.get_yield_name_dict()
        species = context["species"]
        yield_class = context["yield_class"]
        dist = context["dist"]
        disturbance_timing = dataframes["disturbance_timing"]

        try:
            timing_info = disturbance_timing.loc[
                (disturbance_timing.index == yield_name[species][yield_class])
                & (disturbance_timing["disturbance_id"] == dist)
            ]
           
            row_data['sw_age_min'] = int(timing_info['sw_age_min'].item())
            row_data['sw_age_max'] = int(timing_info['sw_age_max'].item())
            row_data['hw_age_min'] = int(timing_info['hw_age_min'].item())
            row_data['hw_age_max'] = int(timing_info['hw_age_max'].item())
            row_data['MinYearsSinceDist'] = int(timing_info['min years since dist'].item())
          
        except (ValueError, KeyError):
            # Default values if any of the above operations fail
            
            row_data['sw_age_min'] = 0
            row_data['sw_age_max'] = 210
            row_data['hw_age_min'] = 0
            row_data['hw_age_max'] = 210
            row_data['MinYearsSinceDist'] = -1
           



