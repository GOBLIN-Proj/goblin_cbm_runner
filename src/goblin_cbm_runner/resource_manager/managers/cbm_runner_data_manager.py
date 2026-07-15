"""
CBM Runner Data Manager
=======================
This module contains the DataManager classes for AF, FM, SC, and DF runners.

Each DataManager loads configuration and provides access methods for its component.
- AFDataManager: Afforestation baseline (database-driven)
- FMDataManager: Forest Management baseline (database-driven)
- SCDataManager: Scenarios (config-driven with database support)
- DFDataManager: Dynamic Forest / NAI continuation (config-driven)
"""
import yaml
import goblin_cbm_runner.resource_manager.utils.parser as parser
import pandas as pd
from goblin_cbm_runner.configuration_data import get_local_dir
from goblin_cbm_runner.resource_manager.loaders import SCLoader
import os


class DataManagerBase:
    """
    Base class for CBM Runner Data Managers.

    Provides common functionality for loading configuration files.
    """

    def get_config_data(self, config_file):
        """
        Load and return configuration data from a YAML file.

        Args:
            config_file (str): Path to the configuration file.

        Returns:
            dict: Configuration data loaded from the file.
        """
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as file:
                config_data = yaml.safe_load(file)
            return config_data
        return {}


class AFDataManager(DataManagerBase):
    """
    Data Manager for Afforestation (AF) Baseline Runner.

    Loads AF_config.yaml for species mappings to CBM defaults.
    AF data comes from database tables (AF_inventory_2100, etc.).
    """

    def __init__(self, sit_path=None):
        """
        Initialize AFDataManager with AF configuration.

        Args:
            sit_path: Path to SIT files (optional)
        """
        self.sit_path = sit_path

        # Load AF config (internal)
        self.cbm_default_config = self.get_config_data(
            os.path.join(get_local_dir(), "AF_config.yaml")
        )

        self.species_mapping = self.cbm_default_config.get("species_mapping", {})
        self.mapping = self.cbm_default_config.get("cbm_mapping", {})

    def get_default_config(self):
        """Get the default configuration data."""
        return self.cbm_default_config

    def get_sit_path(self):
        """Get the path to the SIT file."""
        return self.sit_path

    def get_species_mapping(self):
        """Get the species mapping dictionary."""
        return self.mapping

    def get_cbm_mapping(self):
        """Get the CBM mapping dictionary."""
        return self.mapping

    def get_afforestation_baseline_year(self):
        """Get the afforestation baseline year (1990)."""
        return self.cbm_default_config.get("simulation", {}).get("baseline_year", 1990)

    def get_forest_end_year(self):
        """Get the forest end year."""
        return self.cbm_default_config.get("simulation", {}).get("end_year", 2070)


class FMDataManager(DataManagerBase):
    """
    Data Manager for Forest Management (FM) Baseline Runner.

    Unlike AF, FM manages existing forest from 2016 and requires spinup
    using standing volume data.
    """

    def __init__(self, sit_path=None):
        """
        Initialize FMDataManager with FM configuration.

        Args:
            sit_path: Path to SIT files (optional)
        """
        self.sit_path = sit_path

        # Load FM config
        self.cbm_default_config = self.get_config_data(
            os.path.join(get_local_dir(), "FM_config.yaml")
        )

        self.species_mapping = self.cbm_default_config.get("species_mapping", {})
        self.mapping = self.cbm_default_config.get("cbm_mapping", {})

    def get_default_config(self):
        """Get the default configuration data."""
        return self.cbm_default_config

    def get_sit_path(self):
        """Get the path to the SIT file."""
        return self.sit_path

    def get_species_mapping(self):
        """Get the species mapping dictionary."""
        return self.mapping

    def get_cbm_mapping(self):
        """Get the CBM mapping dictionary."""
        return self.mapping

    def get_disturbance_mapping(self):
        """Get the disturbance mapping dictionary."""
        return self.cbm_default_config.get("cbm_mapping", {}).get("disturbance_types", {})

    def get_forest_baseline_year(self):
        """Get the forest baseline year (2016)."""
        return self.cbm_default_config.get("simulation", {}).get("baseline_year", 2016)

    def get_forest_end_year(self):
        """Get the forest end year."""
        return self.cbm_default_config.get("simulation", {}).get("end_year", 2070)


class SCDataManager(DataManagerBase):
    """
    Data Manager for Scenario (SC) Runner.

    SC uses a hybrid approach:
    - Database tables for structure (classifiers, transitions, growth curves)
    - User-provided DataFrames for scenario data
    - Simple config dict for delay/rate parameters

    User-provided inputs:
    - scenario_data: Scenario parameters (harvest proportions, etc.)
    - afforest_data: Afforestation areas per scenario
    - config: Dict with afforest_delay and annual_rate_pre_delay
    """

    def __init__(self, scenario_data, afforest_data, config=None, sit_path=None):
        """
        Initialize SCDataManager with user data and config.

        Args:
            scenario_data (pd.DataFrame): Scenario parameters DataFrame
            afforest_data (pd.DataFrame): Afforestation areas per scenario
            config (dict): Configuration dict with keys:
                - afforest_delay (int): Years before scenario rates kick in
                - annual_rate_pre_delay (float): Ha/year during delay period
            sit_path (str): Path to SIT files (optional)
        """
        self.scenario_data = scenario_data
        self.afforest_data = afforest_data
        self.config = config or {}
        self.sit_path = sit_path

        # Load SC_config.yaml (internal static mappings)
        self.cbm_default_config = self.get_config_data(
            os.path.join(get_local_dir(), "SC_config.yaml")
        )

        # Initialize loader for database access
        self.sc_loader = SCLoader()

        # Extract commonly used mappings
        self.mapping = self.cbm_default_config.get("cbm_mapping", {})

        # Build transition and yield mappings from database
        self._build_mappings_from_database()

    def _build_mappings_from_database(self):
        """
        Build transition and yield mappings from SC_transitions_2100.

        Creates:
        - _transition_dict_species: {NF_species: forested_species}
        - _species_to_yield_dict: {forested_species: [yield_classes]}
        - _yield_name_dict: {forested_species: {yield_class: cohort}}
        """
        transitions_df = self.sc_loader.get_transitions()

        # Filter to DISTID4 (afforestation) transitions only
        affor_transitions = transitions_df[
            transitions_df["Dist_Type_ID"] == "DISTID4"
        ]

        # Build NF_* to forested species mapping
        self._transition_dict_species = {}
        for _, row in affor_transitions.iterrows():
            nf_species = row["from_Classifier1"]
            forested_species = row["to_Classifier1"]
            self._transition_dict_species[nf_species] = forested_species

        # Build species to yield classes mapping
        # Group by forested species and collect yield classes
        self._species_to_yield_dict = {}
        for _, row in affor_transitions.iterrows():
            forested_species = row["to_Classifier1"]
            yield_class = row["to_Classifier4"]
            if forested_species not in self._species_to_yield_dict:
                self._species_to_yield_dict[forested_species] = []
            if yield_class not in self._species_to_yield_dict[forested_species]:
                self._species_to_yield_dict[forested_species].append(yield_class)

        # Build yield name dict (identity mapping: cohort = species)
        # The Disturbance_timing cohort names match the forested species names
        self._yield_name_dict = {}
        for forested_species, yield_classes in self._species_to_yield_dict.items():
            self._yield_name_dict[forested_species] = {
                yc: forested_species for yc in yield_classes
            }

    # =========================================================================
    # CORE DATA ACCESS
    # =========================================================================

    def get_afforest_data(self):
        """Get the afforestation data DataFrame."""
        return self.afforest_data

    def get_scenario_data(self):
        """Get the scenario data DataFrame."""
        return self.scenario_data

    def get_sit_path(self):
        """Get the path to SIT files."""
        return self.sit_path

    # =========================================================================
    # CONFIG PARAMETERS (from config dict)
    # =========================================================================

    def get_afforest_delay(self):
        """Get afforestation delay in years."""
        return self.config.get("afforest_delay", 0)

    def get_annual_rate_pre_delay(self):
        """Get annual afforestation rate during delay period (ha/year)."""
        return self.config.get("annual_rate_pre_delay", 0)

    # =========================================================================
    # SIMULATION SETTINGS (from SC_config.yaml)
    # =========================================================================

    def get_forest_baseline_year(self):
        """Get the forest baseline year."""
        return self.cbm_default_config.get("simulation", {}).get("baseline_year", 2020)

    def get_forest_end_year(self):
        """Get the forest end year."""
        return self.cbm_default_config.get("simulation", {}).get("end_year", 2070)
    
    def get_column_index(self, column_name):
      """
      Retrieves the index of a specified column in the scenario data.

      Args:
         column_name (str): The name of the column.

      Returns:
         int: The index of the column, or None if not found.
      """
      lower_case_columns = [col.lower() for col in self.scenario_data.columns]
      try:
         column_index = lower_case_columns.index(column_name)
         return column_index
      except ValueError:
         return None
    
    def get_scenario_list(self):
      """
      Retrieves a list of all scenarios.

      Returns:
         list: A list of scenario identifiers.
      """
      column_index = self.get_column_index("scenarios")
      matching_column_name = self.scenario_data.columns[column_index]
      return self.scenario_data[matching_column_name].unique().tolist()
    
    def get_afforestation_end_year(self):
      """
      Retrieves the end year for afforestation activities.

      If 'Afforest Year' column is not present in scenario_data,
      falls back to forest_end_year with a warning.

      If Afforest Year exceeds forest_end_year, caps it with a warning.

      Returns:
         int: The afforestation end year.
      """
      import warnings
      forest_end_year = self.get_forest_end_year()

      column_index = self.get_column_index("afforest year")
      if column_index is None:
          # Column not present, fall back to forest end year
          warnings.warn(
              f"'Afforest Year' column not found in scenario_data. "
              f"Falling back to forest_end_year ({forest_end_year}). "
              f"If you expected afforestation to end earlier, add 'Afforest Year' column to your scenario_dataframe.",
              UserWarning
          )
          return forest_end_year

      matching_column_name = self.scenario_data.columns[column_index]
      afforest_year = self.scenario_data[matching_column_name].unique().item()

      # Validate: Afforest Year cannot exceed forest end year
      if afforest_year > forest_end_year:
          warnings.warn(
              f"'Afforest Year' ({afforest_year}) exceeds forest_end_year ({forest_end_year}). "
              f"Capping afforestation end year to {forest_end_year}.",
              UserWarning
          )
          return forest_end_year

      return afforest_year

    # =========================================================================
    # METHODS FOR AFFORESTATION TRACKER COMPATIBILITY
    # =========================================================================

    def get_classifiers(self):
        """
        Get classifiers in format expected by AfforestationTracker.

        Returns:
            dict: {"Scenario": classifiers_dict}
        """
        return {"Scenario": self.cbm_default_config.get("classifiers", {})}

    def get_transition_dict_species(self):
        """
        Get NF_* to forested species transition mapping.

        Used by AfforestationTracker to convert afforestation species
        to their post-transition (forested) names.

        Returns:
            dict: {NF_species: forested_species}
            e.g., {"NF_Spruce17-20-nothin": "Spruce17-20-nothin"}
        """
        return self._transition_dict_species

    def get_transition_dict_species_to_yield(self):
        """
        Get mapping from forested species to their yield classes.

        Returns:
            dict: {forested_species: [yield_classes]}
            e.g., {"Spruce17-20-nothin": ["YC_17_20"]}
        """
        return self._species_to_yield_dict

    def get_yield_name_dict(self):
        """
        Get mapping from (species, yield_class) to Disturbance_timing cohort.

        For SC, this is an identity mapping because the forested species name
        IS the cohort name in Disturbance_timing.

        Returns:
            dict: {species: {yield_class: cohort}}
            e.g., {"Spruce17-20-nothin": {"YC_17_20": "Spruce17-20-nothin"}}
        """
        return self._yield_name_dict

    # =========================================================================
    # CBM MAPPINGS (from SC_config.yaml)
    # =========================================================================

    def get_cbm_mapping(self):
        """Get the CBM mapping dictionary (species and disturbance mappings)."""
        return self.mapping

    def get_species_mapping(self):
        """Get the species mapping dictionary."""
        return self.mapping.get("species", {})

    def get_disturbance_mapping(self):
        """Get the disturbance mapping dictionary."""
        return self.mapping.get("disturbance_types", {})

    # =========================================================================
    # CLASSIFIERS (from SC_config.yaml)
    # =========================================================================

    def get_scenario_classifiers(self):
        """
        Get the classifiers dictionary.

        Returns:
            dict: Classifiers for scenario forests
        """
        return self.cbm_default_config.get("classifiers", {})

    # =========================================================================
    # COLUMN DEFINITIONS (from SC_config.yaml)
    # =========================================================================

    def get_disturbance_cols(self):
        """Get the disturbance columns list."""
        return self.cbm_default_config.get("disturbance_cols", [])

    def get_static_disturbance_cols(self):
        """Get the static disturbance columns list."""
        return self.cbm_default_config.get("static_disturbance_cols", [])

    def get_transition_cols(self):
        """
        Get the transition columns dictionary.

        Returns:
            dict: {"before_cols": [...], "after_cols": [...]}
        """
        return self.cbm_default_config.get("transition_cols", {})


class DFDataManager(DataManagerBase):
    """
    Data Manager for Dynamic Forest (NAI Continuation) Runner.

    Loads DF_config.yaml for default parameters, then merges with
    user-provided config dict (user values override defaults).

    Unlike AF/FM/SC, DF has no species mappings or database tables.
    It manages the parameters that control NAI-based harvest scheduling
    and dynamic continuation beyond the standard pipeline's end year.
    """

    def __init__(self, config=None):
        """
        Initialize DFDataManager with defaults from DF_config.yaml,
        overridden by any values in the user-provided config dict.

        Args:
            config (dict): User-provided configuration. Keys that match
                DF_config.yaml structure override the defaults.
                Common keys: dynamic_years, harvest_ratio,
                clearfell_thinning_split, scheduled_disturbances,
                species_column, cbm_vars_dump_dir
        """
        self.user_config = config or {}

        # Load DF_config.yaml (internal defaults)
        self.cbm_default_config = self.get_config_data(
            os.path.join(get_local_dir(), "DF_config.yaml")
        )

    # =========================================================================
    # SIMULATION SETTINGS
    # =========================================================================

    def get_dynamic_years(self):
        """
        Get the number of years to simulate beyond the standard end year.

        Returns:
            int: Dynamic continuation years (default: 30)
        """
        return self.user_config.get(
            'dynamic_years',
            self.cbm_default_config.get('simulation', {}).get('dynamic_years', 30)
        )

    def get_spinup_warmup_steps(self, default=0):
        """
        Get the number of growth-only warm-up steps applied before the first
        recorded dynamic timestep.

        Used to settle the AF backward-decomposition spinup's over-inflated
        Litter/Deadwood pools before output is recorded (avoids spurious
        negative flux at the start of the series). The standard-sim pipeline
        passes a small default (3); the FM/AF 2070 continuation leaves it at 0.

        Args:
            default (int): Fallback when neither the user config nor
                DF_config.yaml specifies a value.

        Returns:
            int: Number of warm-up steps.
        """
        return self.user_config.get(
            'spinup_warmup_steps',
            self.cbm_default_config.get('simulation', {}).get(
                'spinup_warmup_steps', default
            )
        )

    # =========================================================================
    # HARVEST PARAMETERS
    # =========================================================================

    def get_harvest_ratio(self):
        """
        Get the target proportion of NAI to harvest each year.

        Returns:
            float: Harvest ratio (default: 0.75)
        """
        return self.user_config.get(
            'harvest_ratio',
            self.cbm_default_config.get('harvest', {}).get('harvest_ratio', 0.75)
        )

    def get_clearfell_thinning_split(self):
        """
        Get the clearfell/thinning split proportions.

        Returns:
            dict: Mapping of disturbance type to proportion
                  (default: {'DISTID1': 0.8, 'DISTID2': 0.2})
        """
        return self.user_config.get(
            'clearfell_thinning_split',
            self.cbm_default_config.get('harvest', {}).get(
                'clearfell_thinning_split', {'DISTID1': 0.8, 'DISTID2': 0.2}
            )
        )

    # =========================================================================
    # SCHEDULED DISTURBANCES
    # =========================================================================

    def get_scheduled_disturbances(self):
        """
        Get the list of scheduled (non-harvest) disturbances.

        Returns:
            list: List of dicts with year, disturbance_type, area, and
                  optional species_filter, age_min, age_max
        """
        return self.user_config.get(
            'scheduled_disturbances',
            self.cbm_default_config.get('scheduled_disturbances', [])
        )

    # =========================================================================
    # CLASSIFIER SETTINGS
    # =========================================================================

    def get_species_column(self):
        """
        Get the classifier column name used for species.

        Returns:
            str: Species column name (default: 'Species')
        """
        return self.user_config.get(
            'species_column',
            self.cbm_default_config.get('species_column', 'Species')
        )

    # =========================================================================
    # DIAGNOSTIC SETTINGS
    # =========================================================================

    def get_cbm_vars_dump_dir(self):
        """
        Get the directory for dumping CBMVariables each timestep.

        Returns:
            str or None: Path to dump directory, or None if not set
        """
        return self.user_config.get('cbm_vars_dump_dir', None)
