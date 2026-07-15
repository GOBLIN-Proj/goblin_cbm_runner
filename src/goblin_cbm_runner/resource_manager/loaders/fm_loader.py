"""
FM Loader Module
================
Loader for Forest Management (FM) baseline data.
Reads from FM_* tables in the database.
"""
import pandas as pd
from goblin_cbm_runner.resource_manager.loaders.base import LoaderBase


class FMLoader(LoaderBase):
    """
    Loader for Forest Management (FM) baseline data.

    Reads from database tables:
    - FM_inventory_2100
    - FM_classifiers_2100
    - FM_age_class_2100
    - FM_disturbance_types_2100
    - FM_growth_2100
    - FM_disturbances_2100
    - FM_transition_2100
    - FM_standing_volume_2100
    - FM_HISTORIC_disturbances_2100
    - FM_HISTORIC_transition_2100
    """

    def get_inventory(self) -> pd.DataFrame:
        """Returns the FM inventory dataframe."""
        return self._read_table("FM_inventory_2100")

    def get_classifiers(self) -> pd.DataFrame:
        """Returns the FM classifiers dataframe."""
        return self._read_table("FM_classifiers_2100")

    def get_age_classes(self) -> pd.DataFrame:
        """Returns the FM age classes dataframe."""
        return self._read_table("FM_age_class_2100")

    def get_disturbance_types(self) -> pd.DataFrame:
        """Returns the FM disturbance types dataframe."""
        return self._read_table("FM_disturbance_types_2100")

    def get_growth_curves(self) -> pd.DataFrame:
        """Returns the FM growth curves dataframe."""
        return self._read_table("FM_growth_2100")

    def get_disturbance_events(self) -> pd.DataFrame:
        """Returns the FM disturbance events dataframe."""
        return self._read_table("FM_disturbances_2100")

    def get_transitions(self) -> pd.DataFrame:
        """Returns the FM transitions dataframe."""
        return self._read_table("FM_transition_2100")

    def get_standing_volume(self) -> pd.DataFrame:
        """Returns the FM standing volume dataframe (for spinup)."""
        return self._read_table("FM_standing_volume_2100")

    def get_historic_disturbances(self) -> pd.DataFrame:
        """Returns the FM historic disturbances dataframe (for spinup)."""
        return self._read_table("FM_HISTORIC_disturbances_2100")

    def get_historic_transitions(self) -> pd.DataFrame:
        """Returns the FM historic transitions dataframe (for spinup)."""
        return self._read_table("FM_HISTORIC_transition_2100")
