"""
Data Generator Abstract Base Class
===================================
Defines the contract for all CBM data generators.

Implementations:
- AFDataGenerator: Reads from AF_* database tables
- FMDataGenerator: Reads from FM_* database tables
- SCDataGenerator: Generates from config.yaml
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict


class DataGenerator(ABC):
    """
    Abstract base class for CBM SIT data generation.

    All concrete implementations must provide these methods to generate
    the complete set of SIT (Stand and Inventory Tool) input files required
    by the CBM model.
    """

    @abstractmethod
    def generate_inventory(self, output_path: str) -> pd.DataFrame:
        """
        Generate inventory.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing inventory data

        Required columns:
            - Classifier1, Classifier2, Classifier3, Classifier4 (varies by type)
            - UsingID, Age, Area, Delay
        """
        pass

    @abstractmethod
    def generate_classifiers(self, output_path: str) -> pd.DataFrame:
        """
        Generate classifiers.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing classifier definitions

        Required columns:
            - classifier_id, name, description
        """
        pass

    @abstractmethod
    def generate_age_classes(self, output_path: str) -> pd.DataFrame:
        """
        Generate age_classes.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing age class definitions

        Required columns:
            - id, size
        """
        pass

    @abstractmethod
    def generate_disturbance_events(self, output_path: str) -> pd.DataFrame:
        """
        Generate disturbance_events.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing disturbance event data

        Required columns:
            - Classifier1, Classifier2, Classifier3, Classifier4
            - UsingID, SWStart, SWEnd, HWStart, HWEnd
            - Step, Dist_Type_ID, Amount, etc.
        """
        pass

    @abstractmethod
    def generate_disturbance_types(self, output_path: str) -> pd.DataFrame:
        """
        Generate disturbance_types.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing disturbance type definitions

        Required columns:
            - id, name
        """
        pass

    @abstractmethod
    def generate_transitions(self, output_path: str) -> pd.DataFrame:
        """
        Generate transitions.csv file.

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing transition rules

        Required columns:
            - Classifier1...ClassifierN (before transition)
            - Classifier1...ClassifierN (after transition)
            - DistType, SWStart, SWEnd, HWStart, HWEnd
        """
        pass

    @abstractmethod
    def generate_growth_curves(self, output_path: str) -> pd.DataFrame:
        """
        Generate growth.csv file (yield curves).

        Args:
            output_path: Directory path to save the CSV file

        Returns:
            DataFrame containing growth/yield curve data

        Required columns:
            - Classifier1, Classifier2, Classifier3, Classifier4
            - LeadSpecies
            - Vol0, Vol1, Vol2, ... Vol20 (volume at each age)
        """
        pass

    @abstractmethod
    def generate_config_json(self, output_path: str) -> Dict:
        """
        Generate sit_config.json and spinup_config.json files.

        Args:
            output_path: Directory path to save the JSON files

        Returns:
            Dictionary containing configuration data
        """
        pass

    def generate_all(self, output_path: str) -> None:
        """
        Convenience method to generate all SIT files.

        Args:
            output_path: Directory path to save all files

        Calls all generate_* methods in the correct order.
        """
        self.generate_classifiers(output_path)
        self.generate_age_classes(output_path)
        self.generate_disturbance_types(output_path)
        self.generate_inventory(output_path)
        self.generate_disturbance_events(output_path)
        self.generate_transitions(output_path)
        self.generate_growth_curves(output_path)
        self.generate_config_json(output_path)
