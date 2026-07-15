"""
Loader Module
=============
Main loader facade that combines AF, FM, and SC loaders.
Provides unified access to all database tables.

For new code, prefer using component-specific loaders directly:
- AFLoader for afforestation baseline data
- FMLoader for forest management baseline data
- SCLoader for scenario data

This facade maintains backward compatibility with existing code.
"""
from goblin_cbm_runner.resource_manager.loaders.base import LoaderBase
from goblin_cbm_runner.resource_manager.loaders.af_loader import AFLoader
from goblin_cbm_runner.resource_manager.loaders.fm_loader import FMLoader
from goblin_cbm_runner.resource_manager.loaders.sc_loader import SCLoader


class Loader(LoaderBase):
    """
    Main loader facade combining AF, FM, and SC loaders.

    Provides three ways to access data:
    1. Direct methods (backward compatible): loader.AF_inventory()
    2. Component loaders: loader.af.get_inventory()
    3. Shared data methods: loader.forest_age_structure()

    Attributes:
        af (AFLoader): Afforestation baseline loader
        fm (FMLoader): Forest management baseline loader
        sc (SCLoader): Scenario loader
    """

    def __init__(self, db_path=None):
        """
        Initialize the loader with component loaders.

        Args:
            db_path (str, optional): Path to database file.
        """
        super().__init__(db_path)

        # Component loaders (share the same db_path)
        self.af = AFLoader(db_path)
        self.fm = FMLoader(db_path)
        self.sc = SCLoader(db_path)

    # =========================================================================
    # SHARED DATA (not AF/FM/SC specific)
    # =========================================================================

    def forest_age_structure(self):
        """Returns the forest inventory age structure dataframe."""
        return self._read_table("national_forest_inventory_2017")

    def forest_cbm_yields(self):
        """Returns the forest CBM yields dataframe."""
        return self._read_table("NIR_CBM_YIELD_Parameters")

    def forest_kb_yields(self):
        """Returns the forest KB yields dataframe."""
        return self._read_table("NIR_KB_YIELD_Parameters")

    def NIR_forest_data_ha(self):
        """Returns the NIR forest data (hectares) dataframe."""
        df = self._read_table("forest_data", index_col="year")
        df *= 1000
        return df

    def cso_species_breakdown(self):
        """Returns the CSO species breakdown dataframe."""
        return self._read_table("cso_afforestation_species_proportion", index_col="year")

    def afforestation_areas_NIR(self):
        """Returns the afforestation areas (NIR) dataframe."""
        df = self._read_table("afforestation_NIR", index_col="year")
        df *= 1000
        return df

    def disturbance_time(self):
        """Returns the disturbance times dataframe."""
        return self._read_table("Disturbance_timing", index_col="cohort")

    def kb_yield_curves(self):
        """Returns the KB yield curves dataframe."""
        return self._read_table("KB_yield_curves", index_col="Cohort")

    def kb_standing_vol_yield_curves(self):
        """Returns the KB standing volume yield curves dataframe."""
        return self._read_table("kb_geo_standing_vol", index_col="Cohort")

    def disturbance_type(self):
        """Returns the disturbance types dataframe."""
        return self._read_table("Disturbances")

    def harvest_areas_NIR(self):
        """Returns the forest harvest areas (NIR) dataframe."""
        return self._read_table("forest_harvest_NIR", index_col="year")

    # =========================================================================
    # AF METHODS (backward compatible - delegate to af loader)
    # =========================================================================

    def AF_inventory(self):
        """Returns the AF inventory dataframe."""
        return self.af.get_inventory()

    def AF_classifiers(self):
        """Returns the AF classifiers dataframe."""
        return self.af.get_classifiers()

    def AF_age_class(self):
        """Returns the AF age classes dataframe."""
        return self.af.get_age_classes()

    def AF_disturbance_types(self):
        """Returns the AF disturbance types dataframe."""
        return self.af.get_disturbance_types()

    def AF_growth_curves(self):
        """Returns the AF growth curves dataframe."""
        return self.af.get_growth_curves()

    def AF_disturbances_time_series(self):
        """Returns the AF disturbance events dataframe."""
        return self.af.get_disturbance_events()

    def AF_transition(self):
        """Returns the AF transitions dataframe."""
        return self.af.get_transitions()

    # =========================================================================
    # FM METHODS (backward compatible - delegate to fm loader)
    # =========================================================================

    def FM_inventory(self):
        """Returns the FM inventory dataframe."""
        return self.fm.get_inventory()

    def FM_classifiers(self):
        """Returns the FM classifiers dataframe."""
        return self.fm.get_classifiers()

    def FM_age_class(self):
        """Returns the FM age classes dataframe."""
        return self.fm.get_age_classes()

    def FM_disturbance_types(self):
        """Returns the FM disturbance types dataframe."""
        return self.fm.get_disturbance_types()

    def FM_growth_curves(self):
        """Returns the FM growth curves dataframe."""
        return self.fm.get_growth_curves()

    def FM_disturbances_time_series(self):
        """Returns the FM disturbance events dataframe."""
        return self.fm.get_disturbance_events()

    def FM_transition(self):
        """Returns the FM transitions dataframe."""
        return self.fm.get_transitions()

    def FM_standing_volume(self):
        """Returns the FM standing volume dataframe."""
        return self.fm.get_standing_volume()

    def FM_historic_disturbances(self):
        """Returns the FM historic disturbances dataframe."""
        return self.fm.get_historic_disturbances()

    def FM_historic_transition(self):
        """Returns the FM historic transitions dataframe."""
        return self.fm.get_historic_transitions()

    # =========================================================================
    # SC METHODS (delegate to sc loader)
    # =========================================================================

    def SC_inventory_template(self):
        """Returns the SC inventory template dataframe."""
        return self.sc.get_inventory_template()

    def SC_species_mapping(self):
        """Returns the SC species mapping dataframe."""
        return self.sc.get_species_mapping()

    def SC_species_mapping_dict(self):
        """Returns the SC species mapping as a dictionary."""
        return self.sc.get_species_mapping_dict()

    def SC_classifiers(self):
        """Returns the SC classifiers dataframe."""
        return self.sc.get_classifiers()

    def SC_age_classes(self):
        """Returns the SC age classes dataframe."""
        return self.sc.get_age_classes()

    def SC_disturbance_types(self):
        """Returns the SC disturbance types dataframe."""
        return self.sc.get_disturbance_types()

    def SC_growth_curves(self):
        """Returns the SC growth curves dataframe."""
        return self.sc.get_growth_curves()

    def SC_transitions(self):
        """Returns the SC transitions dataframe."""
        return self.sc.get_transitions()
