"""
Harvest Manager Module 
=======================
This module provides functionalities to manage afforestation and forest disturbance events.
"""
from goblin_cbm_runner.resource_manager.loader import Loader
import pandas as pd


class AfforestationTracker:
    def __init__(self, data_manager, disturdance_dict, forest_df, years):
        """
        Initializes the AfforestationTracker with the given data.

        Parameters:
        - data_manager: An instance of the data manager class.
        - disturdance_dict: Dictionary containing disturbance information.
        - forest_df: DataFrame containing forest data.
        - years: Number of years to run the simulation.
        """
        self.forest_df = forest_df.copy()
        self.years = years
        self.scenario_forest_classifiers = data_manager.get_classifiers()[
            "Scenario"
        ]
        self.species_dict = data_manager.get_transition_dict_species()
        self.species_to_yield_dict = data_manager.get_transition_dict_species_to_yield()
        self.data_manager_class = data_manager
        self.yield_name_dict = self.data_manager_class.get_yield_name_dict()
        self.disturbance_dict = disturdance_dict

        self.loader_class = Loader()
        self.disturbance_timing = self.loader_class.disturbance_time()
        self.disturbance_timing_expanded = self.expand_disturbance_timing()

        self.disturbance_df = pd.DataFrame(columns=["Classifier1", "Classifier2", "Classifier3", "Classifier4", "Amount", "Year", "DistTypeID"])

        #extract disturbances
        self.disturbances = self.extract_disturbance_types()

        # Initialize main stand tracking dataframe
        self.stands_df = self.initialize_stands()


    def initialize_stands(self):
        """
        Initialize the main stands dataframe for either afforestation or standing forest.

        Returns:
        - DataFrame: Initialized stands dataframe.
        """
        stands = self.forest_df.copy()
        # Check if it's afforestation (Classifier2 == "A")
        if (stands["Classifier2"] == "A").all():

            columns = ["Classifier1", "Classifier2", "Classifier3", "Classifier4", "Amount", "Year"]

            stands = stands[columns]

            stands["StandAge"] = 0  # All new afforestation starts at age 0
            stands["Classifier2"] = "L"  # Convert "A" to "L"

            # Apply species transition for afforestation
            stands["Classifier1"] = stands["Classifier1"].map(self.species_dict).fillna(stands["Classifier1"])

        #For standing forest (Classifier2 == "L"), do nothing with Classifier1 or StandAge
        elif (stands["Classifier2"] == "L").all():
            
            columns = ["Classifier1", "Classifier2", "Classifier3", "Classifier4", "Amount", "Year", "StandAge"]

            stands = stands[columns]
            
        else:
            raise ValueError("❌ Input data contains a mix of 'A' and 'L' in Classifier2. This is not allowed.")

        # Ensure LastDist is initialized for all stands
        stands["LastDist"] = None

        return stands
    
    def extract_disturbance_types(self):
        """
        Extracts unique disturbance types from the disturbance_dict.

        Returns:
        - List: Unique disturbance types.
        """
        return list({dist_id for species in self.disturbance_dict for dist_id in self.disturbance_dict[species]})


    def expand_disturbance_timing(self):
        """
        Expand disturbance_timing to include species, yield_class, and proportions from disturbance_dict.

        Returns:
        - DataFrame: Expanded disturbance timing dataframe.
        """
        expanded_rows = []  # To store transformed rows

        for species, yield_classes in self.species_to_yield_dict.items():
            for yield_class in yield_classes:
                cohort_name = self.yield_name_dict.get(species, {}).get(yield_class)
                if not cohort_name:
                    continue  # Skip if mapping is missing

                # Extract all disturbance rules for this cohort
                disturbance_rules = self.disturbance_timing.loc[self.disturbance_timing.index == cohort_name].copy()

                if disturbance_rules.empty:
                    continue  # Skip if no rules found

                # Ensure correct dictionary structure for proportions
                species_disturbances = self.disturbance_dict.get(species, {})
                if not isinstance(species_disturbances, dict):
                    raise TypeError(f"Expected dict for species {species}, got {type(species_disturbances)}: {species_disturbances}")

                # Expand for each disturbance type**
                for dist_id in disturbance_rules["disturbance_id"].unique():
                    proportion = species_disturbances.get(dist_id, 0)

                    # Skip disturbances with zero proportion**
                    if proportion == 0:
                        continue

                    # Create a copy and assign correct proportion
                    temp_rules = disturbance_rules[disturbance_rules["disturbance_id"] == dist_id].copy()
                    temp_rules["proportion"] = proportion
                    temp_rules["Classifier1"] = species  
                    temp_rules["Classifier4"] = yield_class  

                    expanded_rows.append(temp_rules)

        return pd.concat(expanded_rows, ignore_index=True) if expanded_rows else pd.DataFrame()


    def age_stands(self, current_year):
        """
        Ages all stands by one year.

        Parameters:
        - current_year: The current year of the simulation.
        """
        self.stands_df.loc[self.stands_df['Year'] <= current_year, 'StandAge'] += 1


    def apply_disturbance(self, year):
        """
        Apply disturbances based on disturbance timing data in a vectorized way.

        Parameters:
        - year: The current year of the simulation.
        """
        for dist_type in self.disturbances:

            # Merge stands with precomputed `disturbance_timing_expanded`**
            disturbance_cols = ["Classifier1", 
                                "Classifier4", 
                                "disturbance_id", 
                                "sw_age_min", 
                                "sw_age_max", 
                                "hw_age_min", 
                                "hw_age_max", 
                                "min years since dist"
                                ]
            

            merged_df = self.stands_df.merge(
                self.disturbance_timing_expanded[self.disturbance_timing_expanded["disturbance_id"] == dist_type][disturbance_cols],
                on=["Classifier1", "Classifier4"],  # Match by species & yield class
                how="left"
            )

            # Step 2: Identify eligible stands, ensuring clearfelling is applied properly
            eligible_stands = merged_df[
                ((merged_df["StandAge"] >= merged_df["sw_age_min"]) & (merged_df["StandAge"] <= merged_df["sw_age_max"])) &
                (
                    ((merged_df["min years since dist"] == -1) & (merged_df["StandAge"] >= merged_df["sw_age_max"]))  # ✅ Clearfell only if mature
                    | (merged_df["LastDist"].isna())  
                    | ((year - merged_df["LastDist"]) >= merged_df["min years since dist"])  
                )
            ].copy()

            if eligible_stands.empty:
                print(f"No eligible stands found for {dist_type} in Year {year}")
                continue

            # Step 3: Apply disturbances using vectorized operations**
            disturbed_area = eligible_stands["Amount"] * 0.2  
            remaining_area = eligible_stands["Amount"] * 0.8  

            # Step 4: Update the original dataframe**
            self.stands_df.loc[eligible_stands.index, "Amount"] = remaining_area
            self.stands_df.loc[eligible_stands.index, "LastDist"] = year

            # Step 5: Create the new disturbed stands (Vectorized)**
            new_stands = eligible_stands.copy()
            new_stands["Amount"] = disturbed_area
            new_stands["Year"] = year
            new_stands["DistTypeID"] = dist_type
            new_stands["LastDist"] = year

            # Handle Age & Reset Rules**
            new_stands["StandAge"] = new_stands.apply(
                lambda row: 0 if dist_type == "DISTID1" else row["StandAge"], axis=1
            )

            # Step 6: Append new disturbed stands (Vectorized)**
            self.stands_df = pd.concat([self.stands_df, new_stands], ignore_index=True)

            # Step 7: Record disturbance events efficiently**
            agg_disturbance_df = new_stands.groupby(
                ["Year", "Classifier1", "Classifier2", "Classifier3", "Classifier4", "DistTypeID"], as_index=False
            )["Amount"].sum()

            # Concatenate with the existing disturbance_df**
            if self.disturbance_df.empty and not agg_disturbance_df.empty:
                self.disturbance_df = agg_disturbance_df.copy()
            elif not agg_disturbance_df.empty:
                self.disturbance_df = pd.concat([self.disturbance_df, agg_disturbance_df], ignore_index=True)

            # Step 8: Drop merged disturbance columns to prevent `_x`, `_y` issues
            self.stands_df.drop(columns=["disturbance_id", "sw_age_min", "sw_age_max", "hw_age_min", "hw_age_max", "min years since dist"], errors="ignore", inplace=True)

        # Step 9: Aggregate Similar Stands Instead of Removing Small Stands
        aggregation_columns = ["Year", "Classifier1", "Classifier2", "Classifier3", "Classifier4", "StandAge"]
        self.stands_df = self.stands_df.groupby(aggregation_columns, as_index=False).agg({"Amount": "sum", "LastDist": "max"})
        
        # Final Step: Remove empty stands**
        self.stands_df = self.stands_df[self.stands_df["Amount"] > 0]

    def run_simulation(self):
        """
        Runs the simulation for all years and returns the disturbance dataframe.

        Returns:
        - DataFrame: Disturbance dataframe after running the simulation.
        """
        for year in range(1, self.years + 1):
            self.age_stands(year)
            self.apply_disturbance(year)

        return self.disturbance_df  # Return the disturbance dataframe

    def get_stands(self):
        """
        Returns the final stands dataframe.

        Returns:
        - DataFrame: Final stands dataframe.
        """
        return self.stands_df