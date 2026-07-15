"""
AF Loader Module
================
Loader for Afforestation (AF) baseline data.
Reads from AF_* tables in the database.
"""
import pandas as pd
from goblin_cbm_runner.resource_manager.loaders.base import LoaderBase


class AFLoader(LoaderBase):
    """
    Loader for Afforestation (AF) baseline data.

    Reads from database tables:
    - AF_inventory_2100
    - AF_classifier_2100
    - AF_age_classes_2100
    - AF_disturbance_types_2100
    - AF_growth_2100
    - AF_disturbance_2100
    - AF_transitions_2100
    """

    def get_inventory(self) -> pd.DataFrame:
        """Returns the AF inventory dataframe."""
        return self._read_table("AF_inventory_2100")

    def get_classifiers(self) -> pd.DataFrame:
        """Returns the AF classifiers dataframe."""
        return self._read_table("AF_classifier_2100")

    def get_age_classes(self) -> pd.DataFrame:
        """Returns the AF age classes dataframe."""
        return self._read_table("AF_age_classes_2100")

    def get_disturbance_types(self) -> pd.DataFrame:
        """Returns the AF disturbance types dataframe."""
        return self._read_table("AF_disturbance_types_2100")

    def get_growth_curves(self) -> pd.DataFrame:
        """Returns the AF growth curves dataframe."""
        return self._read_table("AF_growth_2100")

    def get_disturbance_events(self) -> pd.DataFrame:
        """Returns the AF disturbance events dataframe."""
        return self._read_table("AF_disturbance_2100")

    def get_transitions(self) -> pd.DataFrame:
        """Returns the AF transitions dataframe."""
        return self._read_table("AF_transitions_2100")
