"""
AF Runner
=========
Simple, focused runner for AF (Afforestation) baseline.

Purpose:
    - Generate AF input data from database
    - Run CBM simulation
    - Return AF baseline carbon stocks and fluxes

Data Source: Database tables (AF_inventory_2100, AF_disturbances_2100, etc.)
Scenarios: -1 only (AF baseline)
Spinup: NO (new afforestation from 1990, starts from bare land)

Comprehensive Mode:
    When comprehensive=True, captures validation tables (pools, flux, state, etc.)
    in addition to aggregated results. Use for validation or NAI calculations.
"""
import os
import pandas as pd
from goblin_cbm_runner.cbm.data_processing.default_processing.af import AFDataGenerator
from goblin_cbm_runner.cbm.methods.cbm_methods import CBMSim
from goblin_cbm_runner.runners.base_runner import BaseRunner
from goblin_cbm_runner.resource_manager import Paths
import logging



class AFRunner(BaseRunner):
    """
    AF (Afforestation) Baseline Runner.

    Simple workflow:
    1. Generate CSV inputs from database
    2. Run CBM simulation
    3. Return results

    Comprehensive Mode:
        Set comprehensive=True to capture validation tables alongside results.
        Access via last_validation_tables after running simulation.
    """

    def __init__(self, data_manager, output_path=None, comprehensive=False):
        """
        Initialize AF runner.

        Args:
            data_manager: DataManager instance with AF config
            output_path: Where to save generated files (default: ./af_output)
            comprehensive: If True, capture validation tables (pools, flux, state, etc.)
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.output_path = output_path if output_path is not None else None
        self.comprehensive = comprehensive

        self.data_manager = data_manager

        self.paths = Paths(sit_path=None, gen_baseline=False)

        # Initialize AF data generator
        self.af_generator = AFDataGenerator(self.data_manager)

        # Initialize CBM simulation
        self.cbm_sim = CBMSim()

        # Years for simulation
        self.calibration_year = data_manager.get_afforestation_baseline_year()
        self.forest_end_year = data_manager.get_forest_end_year()
        self.years = self.forest_end_year - self.calibration_year

        self.year_range = range(self.calibration_year, self.forest_end_year + 1)

        self.SCENARIO = -1  # AF baseline scenario

        # Store last validation tables (populated when comprehensive=True)
        self.last_validation_tables = None

        self.paths.make_base_data_dir()
        self.paths.make_AF_input_data_dir()

    def generate_input_data(self):
        """
        Generate AF input files from database.

        Creates in output_path:
            - inventory.csv
            - classifiers.csv
            - age_classes.csv
            - disturbance_events.csv
            - disturbance_types.csv
            - transitions.csv
            - growth.csv
            - sit_config.json

        NO spinup_config.json (AF doesn't need spinup)
        """
        self.logger.info("Generating AF input data...")

        self.paths.clean_AF_input_data_dir()


        if self.output_path == None:
            self.output_path = self.paths.get_AF_input_data_dir()
        self.logger.info(f"AF input data will be saved to: {self.output_path}")


        # Generate all SIT files
        self.af_generator.generate_all(self.output_path)

        self.logger.info("AF input data generated")


    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Conducts CBM simulations to calculate and aggregate carbon flux data.

        If comprehensive=True, also captures validation tables accessible via
        self.last_validation_tables after this method completes.

        Returns:
            pd.DataFrame: Aggregated carbon flux data across all scenarios.
        """
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        if self.comprehensive:
            # Use comprehensive simulation to capture validation tables
            result = self.cbm_sim.cbm_comprehensive_simulation(
                self.SCENARIO,
                self.paths.set_AF_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_AF_input_data_dir,
                self.paths.get_aidb_path
            )
            forest_data = result['aggregated']
            self.last_validation_tables = result['validation']
        else:
            # Use lightweight simulation (no validation tables)
            forest_data = self.cbm_sim.cbm_aggregate_scenario_stock(
                self.SCENARIO,
                self.paths.set_AF_SIT_data_dir,
                self.years,
                self.year_range,
                self.paths.get_AF_input_data_dir,
                self.paths.get_aidb_path
            )
            self.last_validation_tables = None

        fluxes_data = self.cbm_sim.cbm_scenario_fluxes(forest_data)

        fluxes_forest_data = pd.concat(
            [fluxes_forest_data, fluxes_data], ignore_index=True
        )

        return fluxes_forest_data

    def run_cbm_flux_scenarios(self, by_species=False) -> pd.DataFrame:
        """
        Run AF simulation and return derived CBM flux and soil metrics per year.

        Unlike run_flux_scenarios() which uses stock-delta (pool differences),
        this calls the CBM engine's internal flux table directly — the per-stand,
        per-timestep atmospheric exchange records from cbm_output.flux — then
        applies post-processing to derive Soil and ecosystem metrics.

        Returns two rows per calendar year by default:
          stands="all"          — all stands (NF_ + forest)
          stands="forest_only"  — forest stands only (Species not starting with "NF_")

        With by_species=True, also returns per-species rows (stands=species name).

        Key output columns (all in tC/yr):
          AGB, BGB              — net biomass change (DeltaBiomass_AG/BG)
          Fine_root_litter      — TurnoverFineLitterInput: TOTAL fine root litter (pre-split).
                                  libcbm routes 50% to BGVF and 50% to AGVF internally via
                                  fine_ag_split=0.5 in the AIDB. This column is the total;
                                  Soil_BGVF uses Fine_root_litter × 0.5 as the BGVF input.
          Coarse_root_litter    — TurnoverCoarseLitterInput → BelowGroundFastSoil
          AG_turnover           — TurnoverMerch+Fol+OthLitterInput (AG → DOM)
          BGSlow_decay          — DecaySlowBGToAir (positive = magnitude of loss)
          BGVF_decay            — DecayVFastBGToAir (positive = magnitude of loss)
          Soil_BGVF             — Fine_root_litter × 0.5 − BGVF_decay  (net BGVF stock change)
          Soil_BGSlow           — BGSlow_stock[t] − BGSlow_stock[t−1]  (pool-delta; includes
                                  AGSlow → BGSlow slow mixing at 0.006/yr, no flux column)
          Soil                  — Soil_BGVF + Soil_BGSlow (matches run_flux_scenarios)
          FineRoot_stock        — SoftwoodFineRoots + HardwoodFineRoots (tC pool stock)
          CoarseRoot_stock      — SoftwoodCoarseRoots + HardwoodCoarseRoots (tC pool stock)
          BGVF_stock            — BelowGroundVeryFastSoil pool stock (tC)
          BGSlow_stock          — BelowGroundSlowSoil pool stock (tC)

        For the raw CBM column names without post-processing use run_annual_raw_flux().

        Args:
            by_species (bool): If True, append per-species rows for forest-only stands.

        Returns:
            pd.DataFrame: Rows per year. Default: 2 rows/year. by_species=True: additional
                          rows per (year, species).
        """
        return self.cbm_sim.AF_raw_cbm_flux(
            self.SCENARIO,
            self.paths.set_AF_SIT_data_dir,
            self.years,
            self.year_range,
            self.paths.get_AF_input_data_dir,
            self.paths.get_aidb_path,
            by_species=by_species,
        )

    def run_annual_raw_flux(self, filter_nf=None) -> pd.DataFrame:
        """
        Run AF simulation and return raw CBM engine flux columns per year.

        Unlike run_cbm_flux_scenarios(), this returns the CBM engine's own column
        names (e.g. TurnoverFineLitterInput, DecayVFastBGToAir) with no renaming
        or derived metrics. Use it to inspect exactly what libcbm is reporting, or
        to cross-check the post-processing in run_cbm_flux_scenarios().

        Key output columns (all in tC/yr):
          DeltaBiomass_AG/BG     — net biomass change
          TurnoverFineLitterInput — TOTAL fine root litter (pre fine_ag_split split).
                                   Only 50% enters BGVF; see run_cbm_flux_scenarios()
                                   for the corrected Soil_BGVF = × 0.5 − BGVF_decay.
          TurnoverCoarseLitterInput, TurnoverMerchLitterInput,
          TurnoverFolLitterInput, TurnoverOthLitterInput — litter inputs
          DecayVFastBGToAir, DecayFastBGToAir, DecaySlowBGToAir — BG pool decay
          DecayVFastAGToAir, DecayFastAGToAir, DecaySlowAGToAir — AG pool decay
          DecayMediumToAir       — Medium pool decay
          DecaySWStemSnagToAir, DecaySWBranchSnagToAir,
          DecayHWStemSnagToAir, DecayHWBranchSnagToAir — snag decay
          DisturbanceSoftProduction, DisturbanceHardProduction,
          DisturbanceDOMProduction — harvest removals
          DisturbanceBioCO2/CH4/COEmission — biomass combustion emissions
          DisturbanceDOMCO2/CH4/COEmission — DOM combustion emissions

        All decay columns are positive (magnitude of outflow to atmosphere).

        Args:
            filter_nf (bool or None):
                None  — return both "all" and "forest_only" rows per year (default)
                True  — forest_only only (NF_ stands excluded)
                False — all-stands only (NF_ stands included)

        Returns:
            pd.DataFrame: Rows per year.
                filter_nf=None  → 2 rows/year (stands="all" and "forest_only")
                filter_nf=True  → 1 row/year (stands="forest_only")
                filter_nf=False → 1 row/year (stands="all")
        """
        return self.cbm_sim.AF_annual_raw_flux(
            self.SCENARIO,
            self.paths.set_AF_SIT_data_dir,
            self.years,
            self.year_range,
            self.paths.get_AF_input_data_dir,
            self.paths.get_aidb_path,
            filter_nf=filter_nf,
        )

    def get_validation_tables(self):
        """
        Get validation tables from last comprehensive simulation.

        Returns:
            dict or None: Validation tables if comprehensive=True was used, else None.
                Keys: 'pools', 'flux', 'state', 'area', 'parameters', 'classifiers'
        """
        return self.last_validation_tables

    def run_validation(self):
        """
        Run CBM validation (optional, for debugging).

        Returns:
            dict: Validation dataframes from CBM simulation.
        """
        return self.cbm_sim.cbm_basic_validation(
            self.years,
            self.paths.set_AF_SIT_data_dir,
            self.paths.get_AF_input_data_dir,
            self.paths.get_aidb_path
        )

    def run_standard_flux(self):
        """
        Run CBM standard flux calculation (optional).

        Returns:
            dict: Standard flux results.
        """
        return self.cbm_sim.run_cbm_standard_flux(
            self.years,
            self.paths.set_AF_SIT_data_dir,
            self.paths.get_AF_input_data_dir,
            self.paths.get_aidb_path
        )

