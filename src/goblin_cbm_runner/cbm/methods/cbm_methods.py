"""
============
CBM Methods
============
This module contains methods for running the Carbon Budget Model (CBM) and generating carbon stocks and fluxes for different scenarios.

v0.6.0 Active Methods:
- AF: AF_simulate_stock, AF_simulate_flux, AF_comprehensive_simulation, cbm_aggregate_scenario_stock, cbm_comprehensive_simulation, cbm_basic_validation, run_cbm_standard_flux
- FM: FM_simulate_stock, FM_comprehensive_simulation, cbm_FM_basic_validation
- Shared: cbm_scenario_fluxes, spinup, step

Comprehensive Methods:
- AF_comprehensive_simulation: AF with manual spinup+step, validation tables, and state capture
- cbm_comprehensive_simulation: AF simulation (black box) returning aggregated results + validation tables
- FM_comprehensive_simulation: FM simulation returning aggregated results + validation tables

State-Capturing Methods (for DynamicRunner continuation):
- AF_simulate_stock: AF with manual spinup+step (stores _last_cbm_vars)
- AF_comprehensive_simulation: AF with manual spinup+step + validation tables (stores _last_cbm_vars)
- FM_simulate_stock: FM with manual spinup+step (stores _last_cbm_vars)
- FM_comprehensive_simulation: FM with manual spinup+step + validation tables (stores _last_cbm_vars)

These comprehensive methods run simulation once and capture all outputs, avoiding the need
to run separate validation passes. Validation tables map to Kevin Black's CBM-CFS3 tables:
- pools → tblPoolIndicator
- flux → tblFluxIndicators
- state → tblDisturbanceIndicators
- classifiers → tblUserDefdClasses

Legacy methods are commented out at the bottom of this file.
"""
from libcbm.model.cbm import cbm_simulator
from libcbm.input.sit import sit_cbm_factory
from libcbm.model.cbm import cbm_variables
from libcbm.model.cbm.cbm_output import CBMOutput
from libcbm.storage.backends import BackendType
import pandas as pd
from goblin_cbm_runner.resource_manager import Pools
from goblin_cbm_runner.resource_manager import FluxManager
from libcbm.storage.dataframe import DataFrame
from libcbm.model.cbm.cbm_variables import CBMVariables
from libcbm.input.sit.sit import SIT
from goblin_cbm_runner.cbm_validation.validation import ValidationData
from goblin_cbm_runner.harvest_summary.builder import HarvestSummaryBuilder
import os



class CBMSim:
    """
    A class for running the Carbon Budget Model (CBM) and generating carbon stocks and fluxes for different scenarios.

    v0.6.0 Active Methods:
        Lightweight (aggregated results only):
        - AF_simulate_stock: AF with manual spinup+step (captures state for DynamicRunner)
        - cbm_aggregate_scenario_stock: AF baseline stock simulation (black box, no state capture)
        - FM_simulate_stock: FM baseline with spinup (captures state for DynamicRunner)

        Comprehensive (aggregated + validation tables):
        - AF_comprehensive_simulation: AF with manual spinup+step + validation tables (captures state)
        - cbm_comprehensive_simulation: AF with all validation tables (black box, no state capture)
        - FM_comprehensive_simulation: FM with all validation tables (captures state)

        Utilities:
        - cbm_scenario_fluxes: Calculate fluxes from stock data
        - cbm_basic_validation: AF validation (legacy, use comprehensive instead)
        - cbm_FM_basic_validation: FM validation (legacy, use comprehensive instead)
        - run_cbm_standard_flux: AF standard flux
        - spinup: Spinup for existing forest
        - step: Step simulation forward

    Attributes:
        pools: An instance of the Pools class.
        Flux_class: An instance of the FluxManager class.
        AGB: A list of above-ground biomass pools.
        BGB: A list of below-ground biomass pools.
        deadwood: A list of deadwood pools.
        litter: A list of litter pools.
        soil: A list of soil organic matter pools.
    """
    def __init__(self):
        """
        Initialize the CBM simulation helper.

        Sets up the pool and flux managers, caches the pool-group lists
        (AGB/BGB/deadwood/litter/soil) used for aggregation, and initializes the
        state-capture slots (``_last_cbm_vars``, ``_last_sit``,
        ``_last_harvest_summary``) populated after each simulation run.
        """
        self.pools = Pools()
        self.Flux_class = FluxManager()
        self.AGB = self.pools.get_above_ground_biomass_pools()
        self.BGB = self.pools.get_below_ground_biomass_pools()
        self.deadwood = self.pools.get_deadwood_pools()
        self.litter = self.pools.get_litter_pools()
        self.soil = self.pools.get_soil_organic_matter_pools()

        # State capture for FM simulations (populated after step loop)
        self._last_cbm_vars = None
        self._last_sit = None

        # Harvest summary (populated after each simulation)
        self._last_harvest_summary = None

    def get_final_cbm_vars(self):
        """Return the final CBMVariables from the last FM or AF simulation, or None."""
        return self._last_cbm_vars

    def get_last_sit(self):
        """Return the last SIT used in the FM and AF step loop, or None."""
        return self._last_sit

    # =========================================================================
    # SHARED METHODS - v0.6.0 Active
    # =========================================================================

    def cbm_scenario_fluxes(self, forest_data):
        """
        Calculate the carbon fluxes for each scenario in the given forest data.

        DECIDED 2026-06-17 — do not re-litigate without re-reading this note first:
        the calibration year (timestep 0) is NOT emitted as a row here. There is
        nothing before it to diff against, and no disturbance ever fires before
        timestep 1, so it would only ever be an all-zero placeholder. The flux
        series starts at calibration_year + 1 (timestep 1, the first real change).
        This matches Kevin Black's own CFS3 reporting shape (he never reports a
        timestep-0 baseline either) — his first reported row should be matched
        against *our* first row directly, no shifting required.

        Args:
            forest_data (pd.DataFrame): DataFrame containing forest data.

        Returns:
            pd.DataFrame: DataFrame containing the calculated fluxes.
        """
        fluxes = pd.DataFrame(columns=forest_data.columns)

        for i in forest_data.index[1:]:
            fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i, "Year"])
            fluxes.loc[i - 1, "Scenario"] = int(forest_data.loc[i, "Scenario"])
            fluxes.loc[i - 1, "AGB"] = (
                forest_data.loc[i, "AGB"] - forest_data.loc[i - 1, "AGB"]
            )
            fluxes.loc[i - 1, "BGB"] = (
                forest_data.loc[i, "BGB"] - forest_data.loc[i - 1, "BGB"]
            )
            fluxes.loc[i - 1, "Deadwood"] = (
                forest_data.loc[i, "Deadwood"] - forest_data.loc[i - 1, "Deadwood"]
            )
            fluxes.loc[i - 1, "Litter"] = (
                forest_data.loc[i, "Litter"] - forest_data.loc[i - 1, "Litter"]
            )
            fluxes.loc[i - 1, "Soil"] = (
                forest_data.loc[i, "Soil"] - forest_data.loc[i - 1, "Soil"]
            )
            fluxes.loc[i - 1, "Harvest"] = (
                forest_data.loc[i, "Harvest"] - forest_data.loc[i - 1, "Harvest"]
            )
            fluxes.loc[i - 1, "Total Ecosystem"] = (
                forest_data.loc[i, "Total Ecosystem"]
                - forest_data.loc[i - 1, "Total Ecosystem"]
            )

        return fluxes

    def spinup(self, sit: SIT,
                classifiers: DataFrame,
                inventory: DataFrame) -> CBMVariables:
        """
        Spin up the CBM model.

        Args:
            sit (SIT): The SIT object.
            classifiers (DataFrame): The classifiers.
            inventory (DataFrame): The inventory.
        """

        with sit_cbm_factory.initialize_cbm(sit) as cbm:

            cbm_vars = cbm_variables.initialize_simulation_variables(
                classifiers,
                inventory,
                cbm.pool_codes,
                cbm.flux_indicator_codes,
                inventory.backend_type,
            )

            spinup_vars = cbm_variables.initialize_spinup_variables(
                cbm_vars,
                inventory.backend_type,
                spinup_params=None, # if you are setting non-default mean annual temperature this may be important
                include_flux=False,
            )

            cbm.spinup(spinup_vars)

            if "mean_annual_temp" in spinup_vars.parameters.columns:
                # since the mean_annual_temp appears in the spinup parameters, carry
                # it forward to the simulation period so that we have consistent
                # columns in the outputs
                cbm_vars.parameters.add_column(
                    spinup_vars.parameters["mean_annual_temp"],
                    cbm_vars.parameters.n_cols,
                )
            cbm_vars = cbm.init(cbm_vars)

            return cbm_vars


    def step(self, time_step: int, sit: SIT, cbm_vars: CBMVariables) -> CBMVariables:
        """
        Step the CBM model forward one timestep.

        Args:
            time_step (int): The timestep.
            sit (SIT): The SIT object.
            cbm_vars (CBMVariables): The CBM variables.
        """
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
            # apply rule based disturbances to the cbm_vars for this timestep
            cbm_vars = rule_based_processor.pre_dynamics_func(time_step, cbm_vars)
            # advance the C dynamics
            cbm_vars = cbm.step(cbm_vars)
            return cbm_vars

    # =========================================================================
    # AF (AFFORESTATION) METHODS - v0.6.0 Active
    # =========================================================================

    def AF_simulate_stock(self, scenario, SIT, years, year_range, input_path, database_path):
        """
        Runs a baseline AF (Afforestation) simulation using the CBM model.

        Unlike FM_simulate_stock, AF uses a SINGLE SIT for both spinup and stepping.
        AF has no separate spinup config (no standing volume). The spinup still runs
        to establish initial soil pools from the afforestation_pre_type (bare land),
        but it uses the same SIT as the step loop.

        Args:
            scenario (int): The scenario identifier (typically -1 for AF baseline).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated AF carbon stocks.
        """

        print(f"Starting AF Simulation...")

        config_input_path = input_path()
        database = database_path()

        # AF uses ONE SIT for both spinup and stepping (no separate spinup config)
        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names)

        # spinup() initializes simulation variables and establishes initial soil pools.
        # For AF, this sets up the afforestation_pre_type soil conditions (bare land).
        # Same sit is used for spinup and stepping.
        cbm_vars = self.spinup(sit, classifiers, inventory)
        # Append t=0 (post-spinup state) to match cbm_simulator.simulate behavior
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        # Store final state for potential continuation (e.g., DynamicRunner)
        self._last_cbm_vars = cbm_vars
        self._last_sit = sit

        pi = cbm_output.classifiers.to_pandas().merge(
            cbm_output.pools.to_pandas(),
            left_on=["identifier", "timestep"],
            right_on=["identifier", "timestep"]
        )

        # NOTE on NF_ stands and soil accounting:
        # NF_ stands hold the afforestation_initial_pool soil values assigned at simulation
        # start. When DISTID4 fires, the stand is reclassified (NF_Cbmix-Bl → Cbmix-Bl) and
        # the soil pool carries over to the new forest stand. Filtering NF_ from the stock
        # calculation while keeping the newly afforested stands would count the soil inheritance
        # as a large positive annual flux (the old NF_ soil appearing in forest accounting),
        # which is misleading. Kevin Black's "exclude NF types / land class 0 and 7" filter
        # is designed for CBM-CFS3 where NF_ stands carry no soil — applying it in libcbm
        # without correction gives the wrong result. The correct approach is to include all
        # stands (NF_ + forest) so that the NF_ decomposition and forest soil inheritance
        # cancel out, giving the true net change in ecosystem soil carbon.
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),
            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = scenario

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=sit.disturbance_id_map,
            disturbance_name_map=sit.disturbance_name_map,
        )

        print(f"AF Simulation Complete.")

        return annual_carbon_stocks

    def AF_simulate_flux(self, scenario, SIT, years, year_range, input_path, database_path):
        """
        Runs AF simulation and returns flux-table-based flux aggregated by FluxManager.

        Unlike AF_simulate_stock (pool-delta), this method uses the libcbm flux table
        — actual atmospheric exchanges recorded per stand per timestep — filtered to
        forest-classified stands (LandClassID 0 or 7). This matches Kevin Black's
        forest-only decomposition reporting and is immune to pool-reclassification
        artefacts that occur when NF_ stands transition to forest via DISTID4.

        Does NOT replace AF_simulate_stock. Use alongside it for validation.

        Args:
            scenario (int): The scenario identifier (typically -1 for AF baseline).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): The number of years to simulate.
            year_range (list): The range of years (e.g. 1990–2070).
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            pandas.DataFrame: Flux DataFrame with columns TimeStep, DeltaBio, DeltaDOM,
                Delta_Ecos, Harvest, Year, Scenario — filtered to LandClassID 0/7.
        """
        print(f"Starting AF Flux Simulation...")

        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map,
        )

        cbm_vars = self.spinup(sit, classifiers, inventory)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        self._last_cbm_vars = cbm_vars
        self._last_sit = sit

        flux = cbm_output.flux.to_pandas()
        state = cbm_output.state.to_pandas()
        parameters = cbm_output.parameters.to_pandas()

        # Aggregate via FluxManager with LandClassID 0/7 filter
        flux_df = self.Flux_class.concatenated_fluxes_data(flux, state, parameters, parameters)
        flux_results = self.Flux_class.flux_filter_and_aggregate(flux_df)
        flux_results = flux_results.reset_index()

        # Map libcbm timestep (1-based) to calendar years
        timestep_to_year = {t: y for t, y in enumerate(year_range)}
        flux_results["Year"] = flux_results["TimeStep"].map(timestep_to_year)
        flux_results["Scenario"] = scenario

        print(f"AF Flux Simulation Complete.")

        return flux_results

    def AF_raw_cbm_flux(self, scenario, SIT, years, year_range, input_path, database_path, by_species=False):
        """
        Run AF simulation and return raw CBM engine flux columns per year.

        Unlike AF_simulate_stock (pool-delta / stock-delta method), this uses
        cbm_output.flux.to_pandas() directly — the CBM engine's own per-stand,
        per-timestep atmospheric exchange records. Does NOT use FluxManager.

        Returns two rows per calendar year by default: one for all stands (stands="all")
        and one for forest-only stands (stands="forest_only", i.e. Species not starting
        with "NF_"). Pass by_species=True to also get per-species rows (stands=species name).

        Flux columns:
          Year, Scenario, stands,
          AGB               — DeltaBiomass_AG (net AG biomass change)
          BGB               — DeltaBiomass_BG (net BG biomass change)
          Fine_root_litter  — TurnoverFineLitterInput: TOTAL fine root litter (pre-split),
                              = fine_root_biomass × 0.641 × temp_adj. libcbm internally routes
                              (1 − fine_ag_split) = 0.5 of this to BGVF and 0.5 to AGVF.
          Coarse_root_litter— TurnoverCoarseLitterInput → BelowGroundFastSoil
          AG_turnover       — TurnoverMerch+Fol+OthLitterInput (AG → DOM)
          BGSlow_decay      — DecaySlowBGToAir (positive, magnitude of BGSlow → atmosphere)
          BGVF_decay        — DecayVFastBGToAir (positive, magnitude of BGVF → atmosphere)
          BGFast_decay      — DecayFastBGToAir
          AGSlow_decay      — DecaySlowAGToAir
          Snag_decay        — sum of 4 StemSnag/BranchSnag decay columns
          Harvest           — DisturbanceSoft+Hard+DOMProduction
          BioAtm            — DisturbanceBioCO2+CH4+CO
          DOMAtm            — DisturbanceDOMCO2+CH4+CO
          Soil_BGVF         — Fine_root_litter × 0.5 − BGVF_decay  (net BGVF stock change;
                              ×0.5 = fraction routed to BGVF by fine_ag_split=0.5 in AIDB)
          Soil_BGSlow       — BGSlow_stock[t] − BGSlow_stock[t−1]  (pool-delta; includes slow
                              mixing from AGSlow → BGSlow at 0.006/yr which has no flux column)
          Soil              — Soil_BGVF + Soil_BGSlow  (matches run_flux_scenarios pool-delta)
          Total_Eco         — biomass net + BG litter + AG turnover − all decay − harvest − atm losses

        Pool stock columns (from pools table, same year as flux):
          FineRoot_stock    — SoftwoodFineRoots + HardwoodFineRoots (tC, standing fine root biomass)
          CoarseRoot_stock  — SoftwoodCoarseRoots + HardwoodCoarseRoots
          BGVF_stock        — BelowGroundVeryFastSoil (tC)
          BGSlow_stock      — BelowGroundSlowSoil (tC)

        NOTES:
        - TurnoverFineLitterInput is TOTAL fine root litter production (pre-split). libcbm
          applies fine_ag_split=0.5 internally: 50% → AGVF (litter layer), 50% → BGVF (soil).
          Soil_BGVF multiplies Fine_root_litter by 0.5 to use only the BGVF portion.
          Fine root biomass = Fine_root_litter / 0.641 — or read FineRoot_stock directly.
        - Slow mixing (AboveGroundSlowSoil → BelowGroundSlowSoil at 0.006/yr) is an internal
          DOM transfer with no named flux column. Soil_BGSlow uses pool-delta (BGSlow_stock[t]
          − BGSlow_stock[t−1]) to capture both BGSlow decay and slow mixing in one step. This
          makes Soil consistent with run_flux_scenarios (pool-delta method).
        - Decay columns (BGSlow_decay, BGVF_decay, etc.) are stored as POSITIVE values (magnitude
          of outflow to atmosphere). Soil_BGVF = Fine_root_litter − BGVF_decay (both positive).
        - NF_ stands contribute zero Fine_root_litter and zero BGVF flux (confirmed: no trees,
          no root litter production). Use stands="forest_only" or by_species=True to see this.

        Args:
            scenario (int): Scenario identifier (typically -1 for AF baseline).
            SIT: Callable returning (sit, classifiers, inventory).
            years (int): Number of years to simulate.
            year_range (list): Calendar years corresponding to timesteps 1..years.
            input_path: Callable returning path to SIT CSV directory.
            database_path: Callable returning path to AIDB.
            by_species (bool): If True, append per-species rows (stands=species name) for
                forest-only stands. Useful for cross-checking Kevin's per-species data.

        Returns:
            pd.DataFrame: Rows per year. Default: 2 rows/year (all + forest_only).
                          With by_species=True: additional rows per (year, species).
        """
        print("Starting AF Raw CBM Flux extraction...")

        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map,
        )

        cbm_vars = self.spinup(sit, classifiers, inventory)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        self._last_cbm_vars = cbm_vars
        self._last_sit = sit

        clf = cbm_output.classifiers.to_pandas()
        flx = cbm_output.flux.to_pandas()
        pls = cbm_output.pools.to_pandas()

        # Join classifiers onto flux and pools; flag NF_ stands
        pi = clf.merge(flx, on=["identifier", "timestep"])
        pi["is_nf"] = pi["Species"].astype(str).str.startswith("NF_")
        pi = pi[pi["timestep"] >= 1].copy()

        pi_pools = clf.merge(pls, on=["identifier", "timestep"])
        pi_pools["is_nf"] = pi_pools["Species"].astype(str).str.startswith("NF_")
        pi_pools = pi_pools[pi_pools["timestep"] >= 1].copy()

        # Include t=0 for pool-delta at t=1 (no timestep filter)
        pi_pools_t0 = clf.merge(pls, on=["identifier", "timestep"])
        pi_pools_t0["is_nf"] = pi_pools_t0["Species"].astype(str).str.startswith("NF_")

        timestep_to_year = {t: y for t, y in enumerate(year_range)}

        records = []

        for filt_label, flux_df, pool_df, pool_t0_df in [
            ("all",         pi,               pi_pools,                pi_pools_t0),
            ("forest_only", pi[~pi["is_nf"]], pi_pools[~pi_pools["is_nf"]], pi_pools_t0[~pi_pools_t0["is_nf"]]),
        ]:
            agg      = FluxManager.aggregate_cbm_flux(flux_df, ["timestep"])
            pool_agg = FluxManager.aggregate_cbm_pools(pool_df, ["timestep"])
            agg      = FluxManager.derive_flux_metrics(agg, pool_agg, ["timestep"])

            # BGSlow pool-delta: BGSlow_stock[t] - BGSlow_stock[t-1]
            # This includes slow_mixing (AGSlow → BGSlow at 0.006/yr), which is an internal
            # DOM transfer with no named flux column. Without this, Soil_BGSlow = -BGSlow_decay
            # understates BGSlow and gives permanently negative Soil inconsistent with run_flux_scenarios.
            pool_full = FluxManager.aggregate_cbm_pools(pool_t0_df, ["timestep"]).sort_values("timestep")
            pool_full["BGSlow_delta"] = pool_full["BGSlow_stock"].diff()
            agg["Soil_BGSlow"] = agg["timestep"].map(pool_full.set_index("timestep")["BGSlow_delta"])
            agg["Soil"]        = agg["Soil_BGVF"] + agg["Soil_BGSlow"]

            agg["Year"]     = agg["timestep"].map(timestep_to_year)
            agg["Scenario"] = scenario
            agg["stands"]   = filt_label
            records.append(agg)

        if by_species:
            forest_flux   = pi[~pi["is_nf"]]
            forest_pools  = pi_pools[~pi_pools["is_nf"]]
            forest_t0     = pi_pools_t0[~pi_pools_t0["is_nf"]]
            agg      = FluxManager.aggregate_cbm_flux(forest_flux, ["timestep", "Species"])
            pool_agg = FluxManager.aggregate_cbm_pools(forest_pools, ["timestep", "Species"])
            agg      = FluxManager.derive_flux_metrics(agg, pool_agg, ["timestep", "Species"])

            pool_full = FluxManager.aggregate_cbm_pools(forest_t0, ["timestep", "Species"]).sort_values(["Species", "timestep"])
            pool_full["BGSlow_delta"] = pool_full.groupby("Species")["BGSlow_stock"].diff()
            pool_full = pool_full[pool_full["timestep"] >= 1][["timestep", "Species", "BGSlow_delta"]]
            agg = agg.merge(pool_full, on=["timestep", "Species"], how="left")
            agg["Soil_BGSlow"] = agg["BGSlow_delta"]
            agg["Soil"]        = agg["Soil_BGVF"] + agg["Soil_BGSlow"]
            agg = agg.drop(columns=["BGSlow_delta"])

            agg["Year"]     = agg["timestep"].map(timestep_to_year)
            agg["Scenario"] = scenario
            agg["stands"]   = agg["Species"]
            records.append(agg)

        result = pd.concat(records, ignore_index=True)

        front_cols = ["Year", "Scenario", "stands", "stand_count",
                      "AGB", "BGB",
                      "Fine_root_litter", "Coarse_root_litter", "AG_turnover",
                      "BGSlow_decay", "BGVF_decay", "BGFast_decay",
                      "AGSlow_decay", "AGVFast_decay", "AGFast_decay", "Medium_decay",
                      "Snag_decay", "Harvest", "BioAtm", "DOMAtm",
                      "Deadwood", "Litter",
                      "Soil_BGVF", "Soil_BGSlow", "Soil", "Total_Eco",
                      "FineRoot_stock", "CoarseRoot_stock", "BGVF_stock", "BGSlow_stock"]
        # keep only columns that exist (guard against unexpected schema)
        result = result[[c for c in front_cols if c in result.columns]]

        print("AF Raw CBM Flux extraction complete.")
        return result

    def AF_annual_raw_flux(self, scenario, SIT, years, year_range, input_path, database_path, filter_nf=None):
        """
        Run AF simulation and return raw CBM engine flux columns per year.

        Unlike AF_raw_cbm_flux, which renames columns and computes derived Soil
        and Total_Eco metrics, this method returns the CBM engine's own column
        names summed per timestep with no post-processing. Use it to inspect
        exactly what libcbm is reporting, or to verify that post-processing
        in AF_raw_cbm_flux is correct.

        Output columns (all values in tC/yr):
          Year, Scenario, stands         — row identifiers
          stand_count                    — unique stands aggregated in this row
          DeltaBiomass_AG                — net aboveground biomass change
          DeltaBiomass_BG                — net belowground biomass change
          TurnoverFineLitterInput        — TOTAL fine root litter entering soil pools
                                           (pre fine_ag_split). libcbm routes 50% to
                                           BelowGroundVeryFastSoil (BGVF) and 50% to
                                           AboveGroundVeryFastSoil (AGVF) internally,
                                           so only half of this value enters BGVF.
                                           Derivation: fine_root_biomass × 0.641 × temp_adj.
          TurnoverCoarseLitterInput      — coarse root litter → BelowGroundFastSoil
          TurnoverMerchLitterInput       — merchantable biomass turnover → StemSnag (natural mortality)
          TurnoverFolLitterInput         — foliage turnover → AboveGroundVeryFastSoil
          TurnoverOthLitterInput         — other biomass turnover → BranchSnag/AGFast
          DisturbanceMerchLitterInput    — merchantable residue entering DOM from a harvest event.
                                           Same source pools as TurnoverMerchLitterInput
                                           (SoftwoodMerch + HardwoodMerch), but sink pools are
                                           disturbance-matrix-dependent: for matrix 16 (clearfell)
                                           the residue fraction routes to MediumSoil; the harvested
                                           fraction is captured in DisturbanceSoftProduction.
          DisturbanceFolLitterInput      — foliage residue entering litter pools from a harvest event
          DisturbanceOthLitterInput      — other wood residue entering litter/DW from a harvest event
                                           (sink pools differ from TurnoverOthLitterInput; proportions
                                           are disturbance-matrix-dependent)
          DisturbanceCoarseLitterInput   — coarse root residue entering soil from a harvest event
          DisturbanceFineLitterInput     — fine root residue entering soil from a harvest event
          NOTE: CBM-CFS3 records a single combined "MerchLitterInput" column covering carbon from
                Merch biomass entering DOM pools from all processes. libcbm splits the same flows
                into TurnoverMerchLitterInput (natural mortality → StemSnags always) and
                DisturbanceMerchLitterInput (harvest event → matrix-defined sink pools). The
                flux_indicator_sink table in the AIDB lists all possible sink pools across all
                disturbance matrices; actual routing in any given simulation is determined by
                which disturbance matrix is applied to the stand.
          DecayVFastBGToAir              — BelowGroundVeryFastSoil decay to atmosphere (positive)
          DecayFastBGToAir               — BelowGroundFastSoil decay to atmosphere (positive)
          DecaySlowBGToAir               — BelowGroundSlowSoil decay to atmosphere (positive).
                                           Does NOT include the AboveGroundSlow → BGSlow slow-
                                           mixing transfer (0.006/yr), which has no flux column
                                           in libcbm. Use pool-delta for net BGSlow change.
          DecayVFastAGToAir              — AboveGroundVeryFastSoil (litter layer) decay to atm
          DecayFastAGToAir               — AboveGroundFastSoil decay to atmosphere
          DecaySlowAGToAir               — AboveGroundSlowSoil decay to atmosphere
          DecayMediumToAir               — Medium pool decay to atmosphere
          DecaySWStemSnagToAir           — softwood stem snag decay to atmosphere
          DecaySWBranchSnagToAir         — softwood branch snag decay to atmosphere
          DecayHWStemSnagToAir           — hardwood stem snag decay to atmosphere
          DecayHWBranchSnagToAir         — hardwood branch snag decay to atmosphere
          DisturbanceSoftProduction      — softwood merchantable carbon removed by harvest
          DisturbanceHardProduction      — hardwood merchantable carbon removed by harvest
          DisturbanceDOMProduction       — DOM/snag carbon removed (e.g. by DISTID7)
          DisturbanceBioCO2Emission      — CO2 from biomass disturbed/combusted
          DisturbanceBioCH4Emission      — CH4 from biomass disturbed/combusted
          DisturbanceBioCOEmission       — CO from biomass disturbed/combusted
          DisturbanceDOMCO2Emission      — CO2 from DOM disturbed/combusted
          DisturbanceDOMCH4Emission      — CH4 from DOM disturbed/combusted
          DisturbanceDOMCOEmission       — CO from DOM disturbed/combusted

        All decay columns are POSITIVE (magnitude of outflow to atmosphere).

        Args:
            scenario (int): Scenario identifier (typically -1 for AF baseline).
            SIT: Callable returning (sit, classifiers, inventory).
            years (int): Number of years to simulate.
            year_range (list): Calendar years corresponding to timesteps 1..years.
            input_path: Callable returning path to SIT CSV directory.
            database_path: Callable returning path to AIDB.
            filter_nf (bool or None):
                None  — return both "all" and "forest_only" rows per year (default)
                True  — forest_only only (Species not starting with "NF_")
                False — all-stands only (NF_ stands included)

        Returns:
            pd.DataFrame: Rows per year.
                filter_nf=None  → 2 rows/year (stands="all" and "forest_only")
                filter_nf=True  → 1 row/year (stands="forest_only")
                filter_nf=False → 1 row/year (stands="all")
        """
        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map,
        )

        cbm_vars = self.spinup(sit, classifiers, inventory)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        clf = cbm_output.classifiers.to_pandas()
        flx = cbm_output.flux.to_pandas()

        pi = clf.merge(flx, on=["identifier", "timestep"])
        pi["is_nf"] = pi["Species"].astype(str).str.startswith("NF_")
        pi = pi[pi["timestep"] >= 1].copy()

        timestep_to_year = {t: y for t, y in enumerate(year_range)}

        raw_cols = [
            "DeltaBiomass_AG", "DeltaBiomass_BG",
            "TurnoverFineLitterInput", "TurnoverCoarseLitterInput",
            "TurnoverMerchLitterInput", "TurnoverFolLitterInput", "TurnoverOthLitterInput",
            "DisturbanceMerchLitterInput", "DisturbanceFolLitterInput",
            "DisturbanceOthLitterInput", "DisturbanceCoarseLitterInput", "DisturbanceFineLitterInput",
            "DecayVFastBGToAir", "DecayFastBGToAir", "DecaySlowBGToAir",
            "DecayVFastAGToAir", "DecayFastAGToAir", "DecaySlowAGToAir", "DecayMediumToAir",
            "DecaySWStemSnagToAir", "DecaySWBranchSnagToAir",
            "DecayHWStemSnagToAir", "DecayHWBranchSnagToAir",
            "DisturbanceSoftProduction", "DisturbanceHardProduction", "DisturbanceDOMProduction",
            "DisturbanceBioCO2Emission", "DisturbanceBioCH4Emission", "DisturbanceBioCOEmission",
            "DisturbanceDOMCO2Emission", "DisturbanceDOMCH4Emission", "DisturbanceDOMCOEmission",
        ]
        available = [c for c in raw_cols if c in pi.columns]

        records = []

        if filter_nf is None or filter_nf is False:
            agg = pi.groupby("timestep")[available].sum().reset_index()
            sc = pi.groupby("timestep")["identifier"].nunique().reset_index().rename(
                columns={"identifier": "stand_count"})
            agg = agg.merge(sc, on="timestep")
            agg["Year"]     = agg["timestep"].map(timestep_to_year)
            agg["Scenario"] = scenario
            agg["stands"]   = "all"
            records.append(agg)

        if filter_nf is None or filter_nf is True:
            filt = pi[~pi["is_nf"]]
            agg = filt.groupby("timestep")[available].sum().reset_index()
            sc = filt.groupby("timestep")["identifier"].nunique().reset_index().rename(
                columns={"identifier": "stand_count"})
            agg = agg.merge(sc, on="timestep")
            agg["Year"]     = agg["timestep"].map(timestep_to_year)
            agg["Scenario"] = scenario
            agg["stands"]   = "forest_only"
            records.append(agg)

        result = pd.concat(records, ignore_index=True)
        front = ["Year", "Scenario", "stands", "stand_count"] + available
        return result[[c for c in front if c in result.columns]]

    def AF_comprehensive_simulation(self, scenario, SIT, years, year_range, input_path, database_path):
        """
        Run AF simulation with manual spinup+step and capture all outputs in a single pass.

        Like AF_simulate_stock, AF uses a SINGLE SIT for both spinup and stepping.
        Like FM_comprehensive_simulation, this captures validation tables alongside
        aggregated results. Also stores _last_cbm_vars and _last_sit for
        DynamicRunner continuation.

        Args:
            scenario (int): The scenario identifier (typically -1 for AF baseline).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            dict: {
                'aggregated': DataFrame with aggregated carbon stocks (same as AF_simulate_stock),
                'validation': {
                    'pools': DataFrame,      # tblPoolIndicator equivalent
                    'flux': DataFrame,       # tblFluxIndicators equivalent
                    'state': DataFrame,      # tblDisturbanceIndicators equivalent
                    'area': DataFrame,       # Area tracking
                    'parameters': DataFrame, # Disturbance parameters
                    'classifiers': DataFrame, # tblUserDefdClasses equivalent
                }
            }
        """
        print(f"Starting AF Comprehensive Simulation...")

        config_input_path = input_path()
        database = database_path()

        # AF uses ONE SIT for both spinup and stepping (no separate spinup config)
        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names)

        # spinup() initializes simulation variables and establishes initial soil pools.
        # For AF, this sets up the afforestation_pre_type soil conditions (bare land).
        # Same sit is used for spinup and stepping.
        cbm_vars = self.spinup(sit, classifiers, inventory)
        # Append t=0 (post-spinup state) to match cbm_simulator.simulate behavior
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        # Store final state for potential continuation (e.g., DynamicRunner)
        self._last_cbm_vars = cbm_vars
        self._last_sit = sit

        # Extract all validation tables
        pools_df = cbm_output.pools.to_pandas()
        flux_df = cbm_output.flux.to_pandas()
        state_df = cbm_output.state.to_pandas()
        area_df = cbm_output.area.to_pandas()
        parameters_df = cbm_output.parameters.to_pandas()
        classifiers_df = cbm_output.classifiers.to_pandas()

        # Create merged primary data (classifiers + pools)
        pi = classifiers_df.merge(
            pools_df,
            left_on=["identifier", "timestep"],
            right_on=["identifier", "timestep"]
        )

        # NOTE on NF_ stands: see AF_simulate_stock for explanation of why we do NOT
        # filter NF_ stands here.

        # Calculate aggregated results (same logic as AF_simulate_stock)
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),
            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = scenario

        print(f"AF Comprehensive Simulation Complete.")

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=sit.disturbance_id_map,
            disturbance_name_map=sit.disturbance_name_map,
        )

        return {
            'aggregated': annual_carbon_stocks,
            'validation': {
                'pools': pools_df,
                'flux': flux_df,
                'state': state_df,
                'area': area_df,
                'parameters': parameters_df,
                'classifiers': classifiers_df,
            }
        }

    def cbm_aggregate_scenario_stock(self, sc, SIT, years, year_range, input_path, database_path):
        """
        Generate carbon stocks for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): Number of years to simulate.
            year_range: Range of years for output.
            input_path: Callable that returns the input path.
            database_path: Callable that returns the database path.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated stocks.
        """

        if sc < 0:
            print(f"Starting AF Simulation...")
        else:
            print(f"Starting Scenario {sc} Simulation...")

        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])

        # NOTE on NF_ stands: see AF_simulate_stock for explanation of why we do NOT
        # filter NF_ stands here. All stands (NF_ + forest) must be included so that
        # NF_ decomposition and forest soil inheritance cancel correctly.

        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest","Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = sc

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=sit.disturbance_id_map,
            disturbance_name_map=sit.disturbance_name_map,
        )

        if sc < 0:
            print(f"AF Simulation Complete.")
        else:
            print(f"Scenario {sc} Simulation Complete.")

        return annual_carbon_stocks

    def cbm_comprehensive_simulation(self, sc, SIT, years, year_range, input_path, database_path):
        """
        Run simulation and capture all outputs in a single pass.

        This method combines the functionality of cbm_aggregate_scenario_stock (for results)
        and cbm_basic_validation (for detailed tables) into a single simulation run.

        Args:
            sc (int): The scenario number (-1 for AF baseline, 0+ for scenarios).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): Number of years to simulate.
            year_range: Range of years for output.
            input_path: Callable that returns the input path.
            database_path: Callable that returns the database path.

        Returns:
            dict: {
                'aggregated': DataFrame with aggregated carbon stocks (same as cbm_aggregate_scenario_stock),
                'validation': {
                    'pools': DataFrame,      # tblPoolIndicator equivalent
                    'flux': DataFrame,       # tblFluxIndicators equivalent
                    'state': DataFrame,      # tblDisturbanceIndicators equivalent
                    'area': DataFrame,       # Area tracking
                    'parameters': DataFrame, # Disturbance parameters
                    'classifiers': DataFrame, # tblUserDefdClasses equivalent
                }
            }
        """
        if sc < 0:
            print(f"Starting AF Comprehensive Simulation...")
        else:
            print(f"Starting Scenario {sc} Comprehensive Simulation...")

        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

        # Simulation - run once, capture everything
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        # Extract all validation tables
        pools_df = cbm_output.pools.to_pandas()
        flux_df = cbm_output.flux.to_pandas()
        state_df = cbm_output.state.to_pandas()
        area_df = cbm_output.area.to_pandas()
        parameters_df = cbm_output.parameters.to_pandas()
        classifiers_df = cbm_output.classifiers.to_pandas()

        # Create merged primary data (classifiers + pools)
        pi = classifiers_df.merge(
            pools_df,
            left_on=["identifier", "timestep"],
            right_on=["identifier", "timestep"]
        )

        # NOTE on NF_ stands: see AF_simulate_stock for explanation of why we do NOT
        # filter NF_ stands here.

        # Calculate aggregated results (same logic as cbm_aggregate_scenario_stock)
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),
            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = sc

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=sit.disturbance_id_map,
            disturbance_name_map=sit.disturbance_name_map,
        )

        if sc < 0:
            print(f"AF Comprehensive Simulation Complete.")
        else:
            print(f"Scenario {sc} Comprehensive Simulation Complete.")

        return {
            'aggregated': annual_carbon_stocks,
            'validation': {
                'pools': pools_df,
                'flux': flux_df,
                'state': state_df,
                'area': area_df,
                'parameters': parameters_df,
                'classifiers': classifiers_df,
            }
        }

    def cbm_basic_validation(self, years, SIT, input_path, database_path):
        """
        Generate validation data for the CBM model for a set of specified inputs.

        Args:
            years (int): The number of years to simulate.
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            input_path: Callable that returns the path to the SIT input data.
            database_path: Callable that returns the path to the database.

        Returns:
            dict: A dictionary containing the generated validation data.
        """

        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])


        si =  cbm_output.state.to_pandas()
        pools = cbm_output.pools.to_pandas()
        flux = cbm_output.flux.to_pandas()
        parameters = cbm_output.parameters.to_pandas()
        area = cbm_output.area.to_pandas()

        state_by_timestep = ValidationData.gen_disturbance_statistics(rule_based_processor, years)

        events = ValidationData.gen_sit_events(rule_based_processor)


        # Merge events and parse, if errors occur, linked_eevents will be None

        try:
            linked_events = ValidationData.merge_disturbances_and_parse(pi,parameters)
        except ValueError as e:
            linked_events = None

        results= {
            "primary_data":pi,
           "data_area":area,
            "data_flux":flux,
            "data_params":parameters,
            "data_pools":pools,
            "data_state":si,
            "events":events,
            "state_by_timestep":state_by_timestep,
            "linked_events":linked_events}

        return results

    def run_cbm_standard_flux(self, years, SIT, input_path, database_path):
        """
        Runs the CBM standard flux.

        Args:
            years (int): The number of years to simulate.
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            dict: A dictionary containing flux results.
        """
        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)


        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )


        flux = cbm_output.flux.to_pandas()


        state_by_timestep = ValidationData.gen_disturbance_statistics(rule_based_processor, years)

        events = ValidationData.gen_sit_events(rule_based_processor)

        pools = cbm_output.pools.to_pandas()
        si =  cbm_output.state.to_pandas()

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])

        merge_state_to_flux = pd.merge(pi, si[["last_disturbance_type", "identifier", "timestep"]], left_on=["identifier", "timestep"], right_on=["identifier", "timestep"], how="left")

        results= {
            "data_flux":flux,
            "events":events,
            "state_by_timestep":state_by_timestep,
            "data_state":si,
            "data_pools":pools,
            "primary_data":pi,
            "merge_state_to_flux":merge_state_to_flux}


        return results

    # =========================================================================
    # FM (FOREST MANAGEMENT) METHODS - v0.6.0 Active
    # =========================================================================

    def FM_simulate_stock(self, scenario, SIT, spinup_SIT, years, year_range, input_path, database_path):
        """
        Runs a baseline (managed) forest simulation using the CBM model.

        Args:
            scenario (int): The scenario identifier (typically -1 for FM baseline).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            spinup_SIT: Callable for spinup that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated managed forest stocks.
        """

        print(f"🚀 Starting FM Simulation...")

        config_input_path = input_path()
        database = database_path()

        spinup_sit, classifiers, inventory = spinup_SIT(config_input_path, database)

        step_sit, redundant_classifier, redundant_inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=spinup_sit.classifier_value_names)

        cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
        # append the t=0 (post-spinup results)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            # the t cbm_vars replace the t-1 cbm_vars
            cbm_vars = self.step(t, step_sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        # Store final state for potential continuation (e.g., DynamicRunner)
        self._last_cbm_vars = cbm_vars
        self._last_sit = step_sit

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])


        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil","Harvest", "Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = scenario

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=step_sit.disturbance_id_map,
            disturbance_name_map=step_sit.disturbance_name_map,
        )

        print(f"FM Simulation Complete.")

        return annual_carbon_stocks

    def FM_comprehensive_simulation(self, scenario, SIT, spinup_SIT, years, year_range, input_path, database_path):
        """
        Run FM simulation and capture all outputs in a single pass.

        This method combines the functionality of FM_simulate_stock (for results)
        and cbm_FM_basic_validation (for detailed tables) into a single simulation run.

        Args:
            scenario (int): The scenario identifier (typically -1 for FM baseline).
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            spinup_SIT: Callable for spinup that takes (path, db_path) and returns (sit, classifiers, inventory).
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            dict: {
                'aggregated': DataFrame with aggregated carbon stocks (same as FM_simulate_stock),
                'validation': {
                    'pools': DataFrame,      # tblPoolIndicator equivalent
                    'flux': DataFrame,       # tblFluxIndicators equivalent
                    'state': DataFrame,      # tblDisturbanceIndicators equivalent
                    'area': DataFrame,       # Area tracking
                    'parameters': DataFrame, # Disturbance parameters
                    'classifiers': DataFrame, # tblUserDefdClasses equivalent
                }
            }
        """
        print(f"🚀 Starting FM Comprehensive Simulation...")

        config_input_path = input_path()
        database = database_path()

        spinup_sit, classifiers, inventory = spinup_SIT(config_input_path, database)
        step_sit, redundant_classifier, redundant_inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=spinup_sit.classifier_value_names)

        # Run spinup and step simulation
        cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            cbm_vars = self.step(t, step_sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)

        # Store final state for potential continuation (e.g., DynamicRunner)
        self._last_cbm_vars = cbm_vars
        self._last_sit = step_sit

        # Extract all validation tables
        pools_df = cbm_output.pools.to_pandas()
        flux_df = cbm_output.flux.to_pandas()
        state_df = cbm_output.state.to_pandas()
        area_df = cbm_output.area.to_pandas()
        parameters_df = cbm_output.parameters.to_pandas()
        classifiers_df = cbm_output.classifiers.to_pandas()

        # Create merged primary data (classifiers + pools)
        pi = classifiers_df.merge(
            pools_df,
            left_on=["identifier", "timestep"],
            right_on=["identifier", "timestep"]
        )

        # Calculate aggregated results (same logic as FM_simulate_stock)
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),
            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest", "Total Ecosystem"]
        ].sum()

        t2y = {t: y for t, y in enumerate(year_range)}
        annual_carbon_stocks["Year"] = annual_carbon_stocks["Year"].map(t2y).astype(int)
        annual_carbon_stocks["Scenario"] = scenario

        # Build harvest summary (lightweight, always-on)
        self._last_harvest_summary = HarvestSummaryBuilder.build(
            cbm_output, year_range,
            disturbance_id_map=step_sit.disturbance_id_map,
            disturbance_name_map=step_sit.disturbance_name_map,
        )

        print(f"✅ FM Comprehensive Simulation Complete.")

        return {
            'aggregated': annual_carbon_stocks,
            'validation': {
                'pools': pools_df,
                'flux': flux_df,
                'state': state_df,
                'area': area_df,
                'parameters': parameters_df,
                'classifiers': classifiers_df,
            }
        }

    def cbm_FM_basic_validation(self, years, SIT, input_path, database_path):
        """
        Runs the CBM Managed Forest validation for the specified years.

        Args:
            years (int): The number of years to simulate.
            SIT: Callable that takes (path, db_path) and returns (sit, classifiers, inventory).
            input_path: Callable that returns the path to the input data.
            database_path: Callable that returns the path to the database.

        Returns:
            dict: A dictionary containing the validation dataframes
        """
        config_input_path = input_path()
        database = database_path()

        sit, classifiers, inventory = SIT(config_input_path, database)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])

        si =  cbm_output.state.to_pandas()
        pools = cbm_output.pools.to_pandas()
        flux = cbm_output.flux.to_pandas()
        parameters = cbm_output.parameters.to_pandas()
        area = cbm_output.area.to_pandas()

        state_by_timestep = ValidationData.gen_disturbance_statistics(rule_based_processor, years)

        events = ValidationData.gen_sit_events(rule_based_processor)

        # Merge events and parse, if errors occur, linked_eevents will be None
        linked_sit = ValidationData.merge_FM_events(events, state_by_timestep)

        results= {
            "primary_data":pi,
            "data_area":area,
            "data_flux":flux,
            "data_params":parameters,
            "data_pools":pools,
            "data_state":si,
            "events":events,
            "state_by_timestep":state_by_timestep,
            "linked_sit":linked_sit}

        return results

    # =========================================================================
    # LEGACY METHODS - Commented out (v0.6.0)
    # These methods use old calling conventions or are superseded.
    # Kept for reference during migration.
    # =========================================================================

    # def get_scenario_afforestation_rates(self,scenario, path):
    #     """
    #     Retrieves afforestation rates for a given scenario.
    #     LEGACY: Uses old file path pattern
    #     """
    #     file_path = os.path.join(path, str(scenario), "disturbance_events.csv")
    #     if not os.path.exists(file_path):
    #         raise FileNotFoundError(f"❌ ERROR: File not found at {file_path}")
    #     disturbances = pd.read_csv(file_path)
    #     required_columns = {"DistTypeID", "Classifier1", "Classifier3", "Classifier4", "Amount", "Year"}
    #     missing_cols = required_columns - set(disturbances.columns)
    #     if missing_cols:
    #         raise ValueError(f"❌ ERROR: Missing required columns in CSV: {missing_cols}")
    #     afforestation = disturbances[disturbances["DistTypeID"] == "DISTID4"].copy()
    #     afforestation["Amount"] = pd.to_numeric(afforestation["Amount"], errors="coerce").fillna(0)
    #     data = {
    #         "scenario": [scenario] * len(afforestation),
    #         "year": afforestation["Year"],
    #         "species": afforestation["Classifier1"],
    #         "yield_class": afforestation["Classifier4"],
    #         "soil": afforestation["Classifier3"],
    #         "afforestation_area": afforestation["Amount"]
    #     }
    #     return pd.DataFrame(data)

    # def cbm_FM_forest_stock(self, cbm_data_class, years, year_range, input_path, database_path):
    #     """
    #     Runs a baseline forest simulation using the CBM model.
    #     LEGACY: Uses old cbm_data_class pattern
    #     """
    #     sit, classifiers, inventory = cbm_data_class.set_baseline_input_data_dir(
    #         input_path, database_path
    #     )
    #     cbm_output = CBMOutput(
    #         classifier_map=sit.classifier_value_names,
    #         disturbance_type_map=sit.disturbance_name_map)
    #     with sit_cbm_factory.initialize_cbm(sit) as cbm:
    #         rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
    #             sit, cbm
    #         )
    #         cbm_simulator.simulate(
    #             cbm,
    #             n_steps=years,
    #             classifiers=classifiers,
    #             inventory=inventory,
    #             pre_dynamics_func=rule_based_processor.pre_dynamics_func,
    #             reporting_func=cbm_output.append_simulation_result,
    #             backend_type=BackendType.numpy
    #         )
    #     pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])
    #     annual_carbon_stocks = pd.DataFrame(
    #         {
    #             "Year": pi["timestep"],
    #             "AGB": pi[self.AGB].sum(axis=1),
    #             "BGB": pi[self.BGB].sum(axis=1),
    #             "Deadwood": pi[self.deadwood].sum(axis=1),
    #             "Litter": pi[self.litter].sum(axis=1),
    #             "Soil": pi[self.soil].sum(axis=1),
    #             "Total Ecosystem": pi[self.AGB + self.BGB + self.deadwood + self.litter + self.soil].sum(axis=1),
    #         }
    #     )
    #     annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
    #         ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
    #     ].sum()
    #     annual_carbon_stocks["Year"] = year_range
    #     return annual_carbon_stocks

    # def libcbm_scenario_fluxes(self, sc, cbm_data_class, years, year_range, input_path, database_path):
    #     """
    #     Generate carbon Fluxes using the Libcbm method for the CBM scenario data.
    #     LEGACY: Uses old cbm_data_class pattern with set_input_data_dir
    #     """
    #     sit, classifiers, inventory = cbm_data_class.set_input_data_dir(sc, input_path, db_path=database_path)
    #     cbm_output = CBMOutput(
    #         classifier_map=sit.classifier_value_names,
    #         disturbance_type_map=sit.disturbance_name_map)
    #     with sit_cbm_factory.initialize_cbm(sit) as cbm:
    #         rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
    #             sit, cbm
    #         )
    #         cbm_simulator.simulate(
    #             cbm,
    #             n_steps=years,
    #             classifiers=classifiers,
    #             inventory=inventory,
    #             pre_dynamics_func=rule_based_processor.pre_dynamics_func,
    #             reporting_func=cbm_output.append_simulation_result,
    #             backend_type=BackendType.numpy
    #         )
    #     flux = cbm_output.flux.to_pandas()
    #     state = cbm_output.state.to_pandas()
    #     parameters = cbm_output.parameters.to_pandas()
    #     area = cbm_output.area.to_pandas()
    #     flux_dataframe = self.Flux_class.concatenated_fluxes_data(flux, state, parameters, area)
    #     flux_results = self.Flux_class.flux_filter_and_aggregate(flux_dataframe)
    #     flux_results["Scenario"] = sc
    #     flux_results["Year"] = year_range[:-1]
    #     annual_process_fluxes = pd.DataFrame(
    #         {
    #             "Scenario": sc,
    #             "Timestep": flux_results.index,
    #             "Year": year_range[:-1],
    #             "DeltaBIO": flux_results["DeltaBio"],
    #             "DeltaDOM": flux_results["DeltaDOM"],
    #             "Harvest": flux_results["Harvest"],
    #             "Total Ecosystem_delta": flux_results["Delta_Ecos"],
    #         }
    #     )
    #     return annual_process_fluxes

    # def FM_simulate_stock_raw_output(self, SIT, spinup_SIT, years, year_range, input_path, database_path):
    #     """
    #     Runs a baseline (managed) forest simulation returning raw output.
    #     LEGACY: Might still be useful for debugging
    #     """
    #     config_input_path = input_path()
    #     database = database_path()
    #     spinup_sit, classifiers, inventory = spinup_SIT(config_input_path, database)
    #     step_sit, redundant_classifier, redundant_inventory = SIT(config_input_path, database)
    #     cbm_output = CBMOutput(classifier_map=spinup_sit.classifier_value_names)
    #     cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
    #     cbm_output.append_simulation_result(0, cbm_vars)
    #     for t in range(1, int(years) + 1):
    #         cbm_vars = self.step(t, step_sit, cbm_vars)
    #         cbm_output.append_simulation_result(t, cbm_vars)
    #     pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])
    #     return pi

    # def cbm_disturbance_area_validation(self, years, input_path, database_path):
    #     """
    #     Generate validation data for area and disturbances.
    #     LEGACY: Uses direct path strings instead of callables
    #     """
    #     sit_config_path = os.path.join(input_path, "sit_config.json")
    #     sit = sit_cbm_factory.load_sit(sit_config_path, database_path)
    #     classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
    #     cbm_output = CBMOutput(
    #         classifier_map=sit.classifier_value_names,
    #         disturbance_type_map=sit.disturbance_name_map)
    #     with sit_cbm_factory.initialize_cbm(sit) as cbm:
    #         rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
    #         cbm_simulator.simulate(
    #             cbm,
    #             n_steps=years,
    #             classifiers=classifiers,
    #             inventory=inventory,
    #             pre_dynamics_func=rule_based_processor.pre_dynamics_func,
    #             reporting_func=cbm_output.append_simulation_result,
    #             backend_type=BackendType.numpy
    #         )
    #     parameters = cbm_output.parameters.to_pandas()
    #     pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])
    #     merge_disturbances_and_parse = ValidationData.merge_disturbances_and_parse(pi, parameters)
    #     return {"merge_disturbances_and_parse": merge_disturbances_and_parse}

    # def scenario_cbm_disturbance_area_validation(self, years, input_path, database_path):
    #     """
    #     Generate validation data for area and disturbances for scenarios.
    #     LEGACY: Uses direct path strings instead of callables
    #     """
    #     sit_config_path = os.path.join(input_path, "sit_config.json")
    #     sit = sit_cbm_factory.load_sit(sit_config_path, database_path)
    #     classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
    #     cbm_output = CBMOutput(
    #         classifier_map=sit.classifier_value_names,
    #         disturbance_type_map=sit.disturbance_name_map)
    #     with sit_cbm_factory.initialize_cbm(sit) as cbm:
    #         rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
    #         cbm_simulator.simulate(
    #             cbm,
    #             n_steps=years,
    #             classifiers=classifiers,
    #             inventory=inventory,
    #             pre_dynamics_func=rule_based_processor.pre_dynamics_func,
    #             reporting_func=cbm_output.append_simulation_result,
    #             backend_type=BackendType.numpy
    #         )
    #     parameters = cbm_output.parameters.to_pandas()
    #     pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])
    #     merge_disturbances_and_parse = ValidationData.default_merge_disturbances_and_parse(pi, parameters)
    #     summary_disturbances = ValidationData.disturbance_summary(pi, parameters)
    #     return {"merge_disturbances_and_parse": merge_disturbances_and_parse, "summary_disturbances": summary_disturbances}

    # def cbm_baseline_disturbance_area_validation(self, years, input_path, database_path):
    #     """
    #     Generate validation data for baseline disturbances.
    #     LEGACY: Uses direct path strings and manual spinup
    #     """
    #     spinup_sit_config_path = os.path.join(input_path, "spinup_config.json")
    #     sit_config_path = os.path.join(input_path, "sit_config.json")
    #     step_sit = sit_cbm_factory.load_sit(sit_config_path, database_path)
    #     spinup_sit = sit_cbm_factory.load_sit(spinup_sit_config_path, database_path)
    #     classifiers, inventory = sit_cbm_factory.initialize_inventory(spinup_sit)
    #     cbm_output = CBMOutput(classifier_map=spinup_sit.classifier_value_names)
    #     cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
    #     cbm_output.append_simulation_result(0, cbm_vars)
    #     for t in range(1, int(years) + 1):
    #         cbm_vars = self.step(t, step_sit, cbm_vars)
    #         cbm_output.append_simulation_result(t, cbm_vars)
    #     parameters = cbm_output.parameters.to_pandas()
    #     pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])
    #     merge_disturbances_and_parse = ValidationData.merge_baseline_disturbances_and_parse(pi, parameters)
    #     return {"merge_baseline_disturbances_and_parse": merge_disturbances_and_parse}

    # def forest_raw_fluxes(self, forest_data):
    #     """
    #     Calculate the carbon fluxes in the given forest data (not aggregated).
    #     LEGACY: Utility method, may still be useful
    #     """
    #     fluxes = pd.DataFrame(columns=forest_data.columns)
    #     columns = ["SoftwoodMerch", "SoftwoodFoliage", "SoftwoodOther", "SoftwoodCoarseRoots",
    #                "SoftwoodFineRoots", "HardwoodMerch", "HardwoodFoliage", "HardwoodOther",
    #                "HardwoodCoarseRoots", "HardwoodFineRoots", "AboveGroundVeryFastSoil",
    #                "BelowGroundVeryFastSoil", "AboveGroundFastSoil", "BelowGroundFastSoil",
    #                "MediumSoil", "AboveGroundSlowSoil", "BelowGroundSlowSoil", "SoftwoodStemSnag",
    #                "SoftwoodBranchSnag", "HardwoodStemSnag", "HardwoodBranchSnag", "CO2",
    #                "CH4", "CO", "NO2", "Products"]
    #     for i in forest_data.index:
    #         if i > 0:
    #             for col in forest_data.columns:
    #                 if col not in columns:
    #                     fluxes.loc[i, col] = forest_data.loc[i, col]
    #             fluxes.loc[i - 1, "timestep"] = int(forest_data.loc[i, "timestep"]) - 1
    #             for column in columns:
    #                 fluxes.loc[i - 1, column] = forest_data.loc[i, column] - forest_data.loc[i - 1, column]
    #         else:
    #             fluxes.loc[i, "timestep"] = int(forest_data.loc[i, "timestep"])
    #             for column in columns:
    #                 fluxes.loc[i, column] = forest_data.loc[i, column]
    #     return fluxes

    # def cbm_FM_summary_fluxes(self, forest_data):
    #     """
    #     Calculate the carbon fluxes for baseline managed forest.
    #     LEGACY: Similar to cbm_scenario_fluxes but without Scenario column
    #     """
    #     fluxes = pd.DataFrame(columns=forest_data.columns)
    #     for i in forest_data.index[1:]:
    #         fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i-1, "Year"])
    #         fluxes.loc[i - 1, "AGB"] = forest_data.loc[i, "AGB"] - forest_data.loc[i - 1, "AGB"]
    #         fluxes.loc[i - 1, "BGB"] = forest_data.loc[i, "BGB"] - forest_data.loc[i - 1, "BGB"]
    #         fluxes.loc[i - 1, "Deadwood"] = forest_data.loc[i, "Deadwood"] - forest_data.loc[i - 1, "Deadwood"]
    #         fluxes.loc[i - 1, "Litter"] = forest_data.loc[i, "Litter"] - forest_data.loc[i - 1, "Litter"]
    #         fluxes.loc[i - 1, "Soil"] = forest_data.loc[i, "Soil"] - forest_data.loc[i - 1, "Soil"]
    #         fluxes.loc[i - 1, "Harvest"] = forest_data.loc[i, "Harvest"] - forest_data.loc[i - 1, "Harvest"]
    #         fluxes.loc[i - 1, "Total Ecosystem"] = forest_data.loc[i, "Total Ecosystem"] - forest_data.loc[i - 1, "Total Ecosystem"]
    #     return fluxes
