"""
SC Loader Module
================
Loader for Scenario (SC) data.
Reads from SC_* tables in the database.

SC is config-driven but uses database tables for:
- Inventory template (all valid combinations with Area=0)
- Species mapping (upstream format → internal format translation)
- Classifiers, age classes, disturbance types (static structure)
"""
import pandas as pd
from goblin_cbm_runner.resource_manager.loaders.base import LoaderBase


class SCLoader(LoaderBase):
    """
    Loader for Scenario (SC) data.

    Reads from database tables:
    - SC_inventory_2100 (template with Area=0)
    - SC_species_mapping (upstream → internal translation)
    - SC_classifiers_2100
    - SC_age_classes_2100
    - SC_disturbance_types_2100
    - SC_growth_2100
    """

    # =========================================================================
    # INVENTORY
    # =========================================================================

    def get_inventory_template(self) -> pd.DataFrame:
        """
        Returns the SC inventory template dataframe.

        This is a pre-populated template with all valid combinations
        and Area=0. Used as starting point for scenario inventory generation.
        """
        return self._read_table("SC_inventory_2100")

    # =========================================================================
    # SPECIES MAPPING (for upstream format translation)
    # =========================================================================

    def get_species_mapping(self) -> pd.DataFrame:
        """
        Returns the SC species mapping dataframe.

        Maps upstream GOBLIN_lite format (species, yield_class) to
        internal classifier names (e.g., Sitka + YC20_24 → NF_Spruce21-24).
        """
        return self._read_table("SC_species_mapping")

    def get_species_mapping_dict(self) -> dict:
        """
        Returns species mapping as a lookup dictionary.

        Returns:
            dict: {(input_species, input_yield_class): internal_classifier1}
        """
        df = self.get_species_mapping()
        return {
            (row.input_species, row.input_yield_class): row.internal_classifier1
            for _, row in df.iterrows()
        }

    # =========================================================================
    # CLASSIFIERS AND STRUCTURE
    # =========================================================================

    def get_classifiers(self) -> pd.DataFrame:
        """Returns the SC classifiers dataframe."""
        return self._read_table("SC_classifier_2100")

    def get_age_classes(self) -> pd.DataFrame:
        """Returns the SC age classes dataframe."""
        return self._read_table("SC_age_classes_2100")

    def get_disturbance_types(self) -> pd.DataFrame:
        """Returns the SC disturbance types dataframe."""
        return self._read_table("SC_disturbance_types_2100")

    def get_growth_curves(self) -> pd.DataFrame:
        """Returns the SC growth curves dataframe."""
        return self._read_table("SC_growth_2100")
    
    def get_transitions(self) -> pd.DataFrame:
        """
        Returns the SC transitions dataframe.
        """
        return self._read_table("SC_transitions_2100")

    # =========================================================================
    # DISTURBANCES
    # =========================================================================

    def get_disturbance_events_template(self) -> pd.DataFrame:
        """
        Returns the SC disturbance events template dataframe.

        This may be a template that gets populated based on scenario parameters.
        """
        return self._read_table("SC_disturbances_2100")


