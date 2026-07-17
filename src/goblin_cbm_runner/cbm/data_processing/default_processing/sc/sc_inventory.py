"""
Scenario Inventory Module 
=========================
This module is responsible for managing scenario inventory data for forest simulation in a CBM (Carbon Budget Modeling) context.
It handles the creation and structuring of inventory data for both baseline and scenario-based simulations.
"""
import pandas as pd
from goblin_cbm_runner.resource_manager import Loader


class SCInventory:
    """
    Manages the inventory data for forest simulation in a CBM (Carbon Budget Modeling) context.

    This class is responsible for managing and processing inventory data, including legacy forest inventory and afforestation data. It handles the creation and structuring of inventory data for both baseline and scenario-based simulations.

    Attributes:
        loader_class (Loader): Instance of the Loader class for loading various data.
        data_manager_class (DataManager): Instance of the DataManager class for managing configuration and data retrieval.
        afforestation_data (dict): Data related to afforestation events.
        age_df (DataFrame): Data structure containing information about forest age.
        baseline_forest_classifiers (dict): Classifiers for the baseline forest scenario.
        scenario_forest_classifiers (dict): Classifiers for different scenario-based forests.
        legacy_year (int): The calibration year.
        soils_dict (dict): Dictionary containing information about different soil types.
        yield_baseline_dict (dict): Dictionary mapping yield classes to their respective baseline proportions nationally.

    Methods:
        make_inventory_structure: Creates an inventory structure based on the given scenario and parameters.
        scenario_inventory: Calculate the afforestation inventory based on the given scenario and inventory dataframe.
        scenario_afforesation_dict: Calculate the areas of afforestation for each yield class and species based on the scenario afforestation areas.
    """
    def __init__(self, data_manager):
        """
        Initializes the SCInventory class with the provided data manager.

        Parameters:
            data_manager (DataManager): Instance of DataManager for managing configuration and data retrieval.
        """
        self.data_manager_class = data_manager
        self.loader_class = Loader()
        self.afforest_data = data_manager.get_afforest_data()
        self.inventory_template = self.loader_class.SC_inventory_template()
        self.species_mapping = self.loader_class.SC_species_mapping()



    def scenario_inventory(self, scenario):
        """
        Calculate the afforestation inventory based on the given scenario and inventory dataframe.
        Parameters:
            scenario (int): The scenario number.
        Returns:
            DataFrame: The calculated inventory dataframe for the scenario.
        """        
        # Load the base inventory template
        inventory_df = self.inventory_template.copy()

        # Convert Area column to float to allow decimal values
        inventory_df["Area"] = inventory_df["Area"].astype(float)

        # Get the afforestation areas for the scenario
        afforestation_areas = self.scenario_afforesation_dict(scenario)

        # Update the inventory dataframe with afforestation areas
        for classifier, area in afforestation_areas.items():
            mask = inventory_df["Classifier1"] == classifier
            inventory_df.loc[mask, "Area"] = area

        #drop zero-area and nan-area rows
        inventory_df = inventory_df[inventory_df["Area"] > 0]

        return inventory_df
    

    def scenario_afforesation_dict(self, scenario):
        """
        Calculate the areas of afforestation for each yield class and species 
        based on the scenario afforestation areas.
        """
        # Filter for the specific scenario
        mask = self.afforest_data["scenario"] == scenario
        scenario_afforestation_areas = self.afforest_data.loc[mask]
        
        # Get the species mapping dictionary
        species_mapping = self.loader_class.SC_species_mapping_dict()
        
        # Build areas dictionary: {internal_classifier1: total_area}
        areas_dict = {}
        
        for _, row in scenario_afforestation_areas.iterrows():
            # Map from input format to internal format
            key = (row["species"], row["yield_class"])
            
            if key in species_mapping:
                internal_classifier = species_mapping[key]
                # Accumulate areas (in case multiple rows map to same classifier)
                areas_dict[internal_classifier] = areas_dict.get(internal_classifier, 0) + row["total_area"]
            else:
                # Optional: log unmapped species/yield combinations
                print(f"Warning: No mapping found for {key}")
        
        return areas_dict