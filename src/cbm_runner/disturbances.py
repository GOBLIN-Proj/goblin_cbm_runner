import cbm_runner.parser as parser
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.loader import Loader
from cbm_runner.inventory import Inventory
import pandas as pd
import itertools
from cbm_runner.harvest import AfforestationTracker



class Disturbances:
    """
    A class to manage disturbances within a CBM (Carbon Budget Modeling) model.

    This class handles various aspects of disturbances including scenario afforestation areas, 
    legacy disturbance afforestation, disturbance structures, and filling data for legacy and 
    scenario-based disturbances.

    Attributes:
        forest_end_year (int): The end year for the forest data.
        calibration_year (int): The year used for calibration.
        loader_class (Loader): An instance of the Loader class.
        data_manager_class (DataManager): An instance of the DataManager class.
        baseline_forest_classifiers (dict): Classifiers for the baseline forest.
        scenario_forest_classifiers (dict): Classifiers for the scenario forest.
        afforestation_data (DataFrame): Dataframe containing afforestation data.
        inventory_class (Inventory): An instance of the Inventory class.
        disturbance_timing (DataFrame): Dataframe containing disturbance timing information.
        disturbance_dataframe (DataFrame): Dataframe containing disturbance data.
        scenario_disturbance_dict (dict): Dictionary containing scenario disturbance information.
        legacy_disturbance_dict (dict): Dictionary containing legacy disturbance information.
        yield_name_dict (dict): Dictionary mapping yields to names.

    Parameters:
        config_path (str): Path to the configuration file.
        calibration_year (int): The year used for calibration.
        forest_end_year (int): The end (targer) year for the forest data.
        afforestation_data (DataFrame): Dataframe containing afforestation data.
        scenario_data (DataFrame): Dataframe containing scenario data.
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
            calibration_year, config_path, scenario_data
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
        self.scenario_disturbance_dict = self.data_manager_class.scenario_disturbance_dict
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
        """
        Calculates the afforestation area for legacy forest over a number of years.

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


    def disturbance_structure(self):
        """
        Creates a dataframe structure for disturbances.

        Returns:
            DataFrame: A dataframe with the structure for disturbances.
        """
        columns = self.data_manager_class.get_disturbance_cols()
        disturbance_df = pd.DataFrame(columns=columns)

        return disturbance_df

    def fill_legacy_data(self):
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
        disturbance_df = self.disturbance_structure()

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
                        row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr+1)
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
                        self._process_row_data(row_data, context, dataframes)
                        data.append(row_data)
                else:    
                    for species in yield_name_dict.keys():
                        classifier_combo = self._get_classifier_combinations(species, dist)
                        for combination in classifier_combo:
                            forest_type, soil, yield_class = combination
                            row_data = self._generate_row(species, forest_type, soil, yield_class, dist, yr+1)
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
                            self._process_row_data(row_data, context, dataframes)
                            data.append(row_data)
        disturbance_df = pd.DataFrame(data)
        disturbance_df = self._drop_zero_area_rows(disturbance_df)
        return disturbance_df
    

    def fill_baseline_forest(self):
        """
        Fills the baseline forest with disturbance data.

        Returns:
            pandas.DataFrame: DataFrame containing disturbance data.
        """

        disturbance_df = self.disturbance_structure()

        legacy_years = self.forest_end_year  - self.forest_baseline_year

        years = list(
            range(1, (legacy_years + 1))
        )

        disturbance_timing = self.disturbance_timing 

        data = []

        tracker = AfforestationTracker()

        self.legacy_disturbance_tracker(tracker, years)

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

        disturbance_df = pd.DataFrame(data)
        disturbance_df = self._drop_zero_area_rows(disturbance_df)

        return disturbance_df


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

        disturbance_df = self.fill_legacy_data()

        legacy_end_year = self.calibration_year - self.forest_baseline_year

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
                                        "age": 0
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
        """
        Process the harvest data for a scenario.

        Args:
            tracker (Tracker): The tracker object used to track forest changes.
            row_data (dict): The data for a single row.
            context (dict): The context containing additional information.

        Returns:
            None
        """
        dist = context["dist"]
        area = row_data["Amount"]
        if dist == "DISTID4" and area != 0:
            self._track_scenario_harvest(tracker, row_data, context)


    def _track_scenario_harvest(self, tracker, row_data, context):
        """
        Track the harvest scenario in the forest model.

        Args:
            tracker (Tracker): The tracker object used to track forest changes.
            row_data (dict): The data for the current row.
            context (dict): The context containing species, yield class, soil, year, harvest proportion, and age.

        Returns:
            None
        """
        area = row_data["Amount"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        time = context["year"]
        factor = context["harvest_proportion"]
        age = context["age"]

        tracker.afforest(area, species, yield_class, soil, age)
        tracker.forest_disturbance(time, species, yield_class, soil, factor)


    def _drop_zero_area_rows(self, disturbance_df):
        """
        Drops rows from the disturbance dataframe where the 'Amount' column is zero.
        
        Parameters:
            disturbance_df (pandas.DataFrame): The disturbance dataframe.
        
        Returns:
            pandas.DataFrame: The disturbance dataframe with zero area rows dropped.
        """
        disturbance_df = disturbance_df[disturbance_df["Amount"] != 0]
        disturbance_df = disturbance_df.reset_index(drop=True)
        disturbance_df = disturbance_df.sort_values(by=["Year"], ascending=True)
        return disturbance_df


    def _get_legacy_classifier_combinations(self):
        """
        Returns all possible combinations of forest keys, soil keys, and yield keys.
        
        Parameters:
            self (Disturbances): The Disturbances object.
        
        Returns:
            combinations (generator): A generator that yields all possible combinations of forest keys, soil keys, and yield keys.
        """
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["L"]
        soil_keys = list(classifiers["Soil classes"].keys())
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_scenario_classifier_combinations(self):
        """
        Generates combinations of scenario, forest, soil, and yield classifiers.

        Returns:
            A generator that yields combinations of scenario, forest, soil, and yield classifiers.
        """
        classifiers = self.scenario_forest_classifiers
        forest_keys = ["A"]
        soil_keys = ["mineral"]
        yield_keys = list(classifiers["Yield classes"].keys())
        return itertools.product(forest_keys, soil_keys, yield_keys)


    def _get_classifier_combinations(self, species, disturbance=None):
        """
        Generates all possible combinations of forest types, soil classes, and yield classes.

        Returns:
            A generator that yields tuples representing the combinations of forest types, soil classes, and yield classes.
        """

        classifiers = self.scenario_forest_classifiers

        if disturbance == "DISTID1" or disturbance == "DISTID2":
            forest_keys = ["L"]
            soil_keys = ["?"]
            yield_keys = list(self.yield_name_dict[species].keys())
            return itertools.product(forest_keys, soil_keys, yield_keys)
        else:
            forest_keys = list(classifiers["Forest type"].keys())
            soil_keys = list(classifiers["Soil classes"].keys())
            yield_keys = list(self.yield_name_dict[species].keys())
            return itertools.product(forest_keys, soil_keys, yield_keys)
    

    def _get_static_defaults(self):
        """
        Get the default values for static disturbance columns.

        Returns:
            dict: A dictionary containing the default values for each static disturbance column.
        """
        static_cols = self.data_manager_class.get_static_disturbance_cols()
        return {col: -1 for col in static_cols}


    def _generate_row(self, species, forest_type, soil, yield_class, dist, yr):
        """
        Generates a row of data for a disturbance event.

        Args:
            species (str): The species of the forest.
            forest_type (str): The type of forest.
            soil (str): The type of soil.
            yield_class (str): The yield class of the forest.
            dist (int): The disturbance type ID.
            yr (int): The year of the disturbance event.

        Returns:
            dict: A dictionary containing the row data for the disturbance event.
        """
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
        """
        Process the row data for a scenario based on the given context and dataframes.

        Args:
            row_data (dict): The row data for the scenario.
            context (dict): The context containing forest type and disturbance information.
            dataframes (dict): The dataframes containing relevant data.

        Returns:
            None
        """
        forest_type = context["forest_type"]
        dist = context["dist"]

        if forest_type == "A" and dist == "DISTID4":
            self._handle_scenario_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_scenario_forest(row_data, context, dataframes)


    def _process_row_data(self, row_data, context, dataframes):
        """
        Process the row data based on the given context and dataframes.

        Args:
            row_data (dict): The row data to be processed.
            context (dict): The context containing forest type and disturbance information.
            dataframes (dict): The dataframes used for processing.

        Returns:
            None
        """

        legacy_afforestation_end_year = self.calibration_year - self.forest_baseline_year
        forest_type = context["forest_type"]
        dist = context["dist"]
        year = context["year"]


        if forest_type == "A" and dist == "DISTID4" and year < legacy_afforestation_end_year:
            print(legacy_afforestation_end_year)
            self._handle_legacy_afforestation(row_data, context, dataframes)
        elif forest_type == "L":
            self._handle_legacy_forest(row_data, context, dataframes)


    def _handle_legacy_scenario_forest(self, row_data, context, dataframes):
        """
        Handles the legacy scenario forest by updating the disturbance timing and setting the amount based on the area.

        Args:
            row_data (dict): The row data for the disturbance.
            context (dict): The context information for the disturbance.
            dataframes (dict): The dataframes containing additional data.

        Returns:
            None
        """
        if context["dist"] == "DISTID4":
            row_data["Amount"] = 0
        else:
            self._update_disturbance_timing(row_data, context, dataframes)
            area = context["area"]

            row_data["Amount"] = area


    def _handle_scenario_afforestation(self, row_data, context, dataframes):
        """
        Handle the scenario of afforestation.

        This method calculates the amount of afforestation based on the given row data, context, and dataframes.
        It retrieves the afforestation inventory, non-forest dictionary, species, yield class, soil, and configuration classifiers from the context and dataframes.
        The amount of afforestation is calculated based on the afforestation value, yield class proportions, and classifier3 value.
        If the classifier3 value matches the soil value, the amount is calculated using the afforestation value and yield class proportions.
        If there is a TypeError during the calculation, the amount is set to 0.
        If the classifier3 value does not match the soil value, the amount is set to 0.

        Parameters:
        - row_data (dict): The row data for the afforestation scenario.
        - context (dict): The context containing additional information for the calculation.
        - dataframes (dict): The dataframes containing the afforestation inventory.

        Returns:
        - None
        """
        afforestation_inventory = dataframes["afforestation_inventory"]
        non_forest_dict = context["non_forest_dict"]
        species = context["species"]
        yield_class = context["yield_class"]
        soil = context["soil"]
        configuration_classifiers = context["configuration_classifiers"]

        row_data["Classifier1"] = non_forest_dict[species][soil]
        afforestation_value = afforestation_inventory[species][soil]

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
        """
        Handles legacy afforestation by updating the row data with the appropriate classifier and amount.

        Args:
            row_data (dict): The row data to be updated.
            context (dict): The context containing species, yield class, year, and soil information.
            dataframes (dict): A dictionary of dataframes containing the legacy afforestation inventory.

        Returns:
            None
        """
        non_forest_dict = self.data_manager_class.get_non_forest_dict()
        legacy_afforestation_inventory = dataframes["legacy_afforestation_inventory"]
        species = context["species"]
        yield_class = context["yield_class"]
        yr = context["year"]
        soil = context["soil"]

        mask = (
            (legacy_afforestation_inventory["species"] == species)
            & (legacy_afforestation_inventory["yield_class"] == yield_class)
            & (legacy_afforestation_inventory["year"] == yr)
            & (legacy_afforestation_inventory["soil"] == soil)
        )
        row_data["Classifier1"] = non_forest_dict[species][soil]
        try:
            row_data["Amount"] = legacy_afforestation_inventory.loc[mask, "area_ha"].item()
        except ValueError:
            row_data["Amount"] = 0
      

    def _handle_legacy_forest(self, row_data, context, dataframes):
        """
        Handles legacy forest data by updating disturbance timing and populating row data with relevant information.

        Args:
            row_data (dict): The row data to be updated with disturbance information.
            context (dict): The context containing relevant information for the disturbance handling.
            dataframes (dict): A dictionary of dataframes containing disturbance data.

        Returns:
            None
        """
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
                row_data["SortType"] = disturbance_dataframe.loc[
                    mask, "SortType"
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
                row_data["SortType"] = disturbance_dataframe.loc[
                    mask, "SortType"
                ].item()
                
            except ValueError:
                row_data["Amount"] = 0

        else:
            row_data["Classifier1"] = species
            row_data["Amount"] = 0

    
    def _update_disturbance_timing(self, row_data, context, dataframes):
        """Retrieve disturbance timing information from the disturbance_timing DataFrame.

        Args:
            row_data (dict): The dictionary containing row data.
            context (dict): The dictionary containing context information.
            dataframes (dict): The dictionary containing dataframes.

        Returns:
            None

        Raises:
            ValueError: If any of the operations fail due to invalid values.
            KeyError: If any of the required keys are not found.

        """
        yield_name = self.yield_name_dict
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
    

    def legacy_disturbance_tracker(self, tracker, years):
        """
        Apply legacy disturbances to the forest tracker.

        Args:
            tracker (object): The forest tracker object.
            years (list): List of years to apply disturbances.

        Returns:
            None
        """

        data_df = self.get_legacy_forest_area_breakdown()
        yield_name_dict = self.yield_name_dict

        for i in data_df.index:
            species = data_df.at[i, "species"]
            yield_class = data_df.at[i, "yield_class"]
            soil = data_df.at[i, "soil"]
            area = data_df.at[i, "area"]
            age = data_df.at[i, "age"]

            tracker.afforest(area, species, yield_class, soil, age)

        for year in years:
            for species in data_df["species"].unique():
                if species != "SGB":
                    for soil in data_df["soil"].unique():
                        for yc in yield_name_dict[species].keys():
                            dist = self.legacy_disturbance_dict
                            tracker.forest_disturbance(year, species, yc, soil, dist)
            tracker.move_to_next_age()
            

