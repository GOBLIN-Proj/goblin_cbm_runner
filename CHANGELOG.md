## [0.6.0] - 2026-07-15

### Added

#### NAI / Dynamic Continuation Module (`nai/`)
- **`NAICalculator`** — Calculates Net Annual Increment per stand and per species from pool
  data. Formula: `NAI[t] = MerchStock[t] − MerchStock[t−1] + Harvest[t]`.
- **`HarvestScheduler`** — Allocates harvest targets across eligible stands based on species
  age windows from the `Disturbance_timing` database table. Resolves species integer
  classifier IDs to names via `species_name_map` for correct eligibility lookup.
- **`DynamicRunner`** — Step-wise CBM simulation loop that continues from a saved
  `CBMVariables` state using NAI-based harvest scheduling instead of a pre-computed
  disturbance schedule. Returns `DynamicSimulationResult` (aggregated stocks, nai_history,
  sustainability_metrics, optional validation tables).
- **First-timestep harvest seeding** — `DynamicRunner.run_from_state()` accepts
  `initial_species_nai` to pre-seed harvests before the first dynamic step, preventing a
  flux spike at the standard/dynamic boundary year.

#### Dynamic Runners (`runners/`)
- **`DynamicFMRunner`** — Subclasses `FMRunner`; adds `get_final_cbm_vars()` and `get_sit()`
  for handing off CBM state to `DynamicRunner`.
- **`DynamicAFRunner`** — Subclasses `AFRunner`; overrides `run_flux_scenarios()` to use
  `AF_simulate_stock` (state-capturing) and exposes the same state-handoff methods.
- **`DynamicStandardRunner`** — Subclasses `StandardRunner`; adds state capture for
  user-CSV workflows.

#### Dynamic Scenario Generator
- **`DynamicScenarioGenerator`** — Extends `NationalScenarioGenerator`; overrides
  `_run_fm_flux_simulation()` and `_run_af_flux_simulation()` to add NAI continuation
  beyond the standard end year. Extends SC `end_year` by `dynamic_years` at construction
  so all three pipelines cover the same time range. Exposes `run_baseline_flux_simulation()`
  for FM + AF only, and `get_fm_dynamic_result()` / `get_af_dynamic_result()` for NAI
  diagnostics.

#### Simulation Archive (`archive/`)
- **`SimulationArchive`** — SQLite-backed archive for all simulation inputs, results, and
  validation data. Stores input CSVs, aggregated results, validation tables, harvest
  summaries, NAI history, sustainability metrics, and metadata in a single `.db` file.
  Table naming convention: `{runner_type}_{table_name}` for inputs,
  `{runner_type}_validation_{table_name}` for validation tables.
  Accessible via `export_archive(path)` / `get_archive()` on all generators.

#### Harvest Summary (`harvest_summary/`)
- **`HarvestSummaryBuilder`** — Always-on (no `comprehensive` flag needed). Builds
  per-species per-timestep disturbance summary (Provided vs Expected, soft/hard breakdown)
  and NAI summary (GrossC, HarvestC, NAI, Harvest ratio) from `CBMOutput`. Archived as
  `{runner_type}_disturbance_summary` and `{runner_type}_nai_summary`.

#### Manual Spinup+Step Pattern (`cbm/methods/cbm_methods.py`)
- **`CBMSim.AF_simulate_stock`** / **`AF_comprehensive_simulation`** — AF simulation using
  explicit `spinup()` → `step()` loop rather than `cbm_simulator.simulate`. Stores
  `_last_cbm_vars` and `_last_sit` for `DynamicRunner` continuation.
- **`CBMSim.FM_simulate_stock`** / **`FM_comprehensive_simulation`** — Same pattern for
  FM baseline. Uses separate `spinup_SIT` and `step_SIT`.
- **`CBMSim.spinup()`** / **`CBMSim.step()`** — Public primitives for the manual loop.

#### AF Flux Inspection Methods (`cbm/methods/cbm_methods.py`)
- **`AF_simulate_flux`** — Returns FluxManager-aggregated flux (DeltaBio, DeltaDOM,
  Delta_Ecos, Harvest) filtered to forest land classes (LandClassID 0/7).
- **`AF_raw_cbm_flux`** — Returns raw CBM engine flux columns per year with renamed
  columns and derived soil metrics (`Soil_BGVF`, `Soil_BGSlow` via pool-delta, `Total_Eco`).
  Supports `by_species=True` for per-species breakdown.
- **`AF_annual_raw_flux`** — Returns CBM engine flux columns with original libcbm names and
  no post-processing, for direct audit of what libcbm reports.

#### FluxManager Static Methods (`resource_manager/managers/flux_manager.py`)
- **`FluxManager.aggregate_cbm_flux(df, group_cols)`** — Aggregates raw flux table into
  renamed summary columns.
- **`FluxManager.aggregate_cbm_pools(df, group_cols)`** — Aggregates pool table into root
  and soil stock columns.
- **`FluxManager.derive_flux_metrics(agg, pool_agg, join_cols)`** — Derives `AG_turnover`,
  `Snag_decay`, `Harvest`, `BioAtm`, `DOMAtm`, `Soil_BGVF`, `Soil_BGSlow`, `Soil`,
  `Total_Eco` from aggregated flux and pool tables.

#### Comprehensive Simulation Mode
- `comprehensive=True` flag on `NationalScenarioGenerator`, `DynamicScenarioGenerator`,
  and individual runners triggers capture of detailed validation tables (pools, flux, state,
  area, parameters, classifiers) alongside aggregated results. Tables map to CBM-CFS3
  `tblPoolIndicator`, `tblFluxIndicators`, `tblDisturbanceIndicators`, `tblUserDefdClasses`.

#### StandardRunner / User-CSV Pipeline (`runners/standard_runner.py`)
- **`StandardRunner`** — Accepts user-provided SIT CSV files with no internal database
  dependency for inventory or growth data. The `ireland_cbm_defaults_v6.1.db` AIDB is still
  required (bundled). Validates required files on `generate_input_data()`. Static mode
  (explicit disturbance schedule) implemented.
- **`StandardSimGenerator`** — Archive-backed orchestrator for `StandardRunner` simulations.
  Mirrors the `NationalScenarioGenerator` interface (`run_flux_simulation()`,
  `export_archive()`). Includes `get_template()` classmethod to copy template CSVs.
- **`DynamicStandardSimGenerator`** — Extends `StandardSimGenerator` with NAI-based
  continuation via `DynamicStandardRunner` + `DynamicRunner`. Supports NAI from day 1
  (`end_year = baseline_year`) or after a static warm-up phase.

#### Data Processing Refactor (`cbm/data_processing/default_processing/`)
- Monolithic `cbm_data_factory.py`, `SC_disturbances.py`, `SC_inventory.py`,
  `disturbance_utils.py`, `transition.py`, `yield_curves.py` replaced by:
  - `base/data_generator.py` — Abstract `DataGenerator` base class
  - `base/common_utils.py` — Shared CSV/data utilities
  - `af/af_data_generator.py` — `AFDataGenerator` (no spinup files)
  - `fm/fm_data_generator.py` — `FMDataGenerator` (generates `standing_vol.csv`,
    `spinup_config.json`)
  - `sc/sc_data_generator.py` — `SCDataGenerator` (merges user data with DB templates)
  - `sc/sc_disturbances.py` — SC disturbance event helpers
  - `sc/sc_inventory.py` — SC inventory helpers

#### DFDataManager
- **`DFDataManager`** — Loads `DF_config.yaml` defaults for NAI continuation; user-provided
  `dynamic_config` dict overrides any key at construction. Parameters: `dynamic_years`,
  `harvest_ratio`, `clearfell_thinning_split`, `scheduled_disturbances`, `species_column`.

#### Database Updates
- Updated to `cbm_runner_database_0.6.2.db`: added NF-peat species, extended
  `Disturbance_timing` table, added `AF_transitions_2100` DISTID7 wildcard transition rule.

### Changed
- **Archive-only output model**: `NationalScenarioGenerator` and all generators no longer
  auto-generate CSV files. Call `export_archive(path)` to save results to a `.db` file.
- **Callable path pattern**: Runners accept `input_path` and `database_path` as callables
  (zero-argument functions returning strings) rather than direct string arguments.
- **Soil accounting** (`AF_simulate_stock`): NF_ stands are included in stock aggregation
  (not filtered out) so that NF_ decomposition and forest soil inheritance cancel correctly.
  Kevin Black's "exclude NF types" filter is designed for CBM-CFS3 where NF_ stands carry
  no soil; applying it in libcbm gives incorrect results.
- **BGSlow pool-delta correction**: `Soil_BGSlow` now computed from pool-delta
  (`BGSlow[t] − BGSlow[t−1]`) rather than `−DecaySlowBGToAir` alone, capturing the
  `AboveGroundSlowSoil → BelowGroundSlowSoil` slow-mixing transfer (0.006/yr) which has
  no named flux column in libcbm.
- **BGVF fine root split**: `Soil_BGVF = TurnoverFineLitterInput × 0.5 − DecayVFastBGToAir`.
  The 0.5 factor reflects the AIDB `fine_ag_split = 0.5` parameter; only half of fine root
  litter enters `BelowGroundVeryFastSoil`.
- **DISTID7 harvest accounting**: DISTID7 (deforestation) exempted from `land_class == 0`
  filter in `HarvestSummaryBuilder` so deforestation harvest is correctly captured in
  HarvestC and NAI formula.

### Fixed
- **DynamicStandardSim negative early-year flux**: the AF backward-decomposition spinup
  over-inflated the Litter and Deadwood pools, which decayed sharply over the first ~3
  timesteps and produced spurious negative flux at the start of the pure-NAI series. Added
  `spinup_warmup_steps` (default 3, growth-only settling steps) to
  `DynamicRunner.run_from_state()`, wired through `DynamicStandardSimGenerator` via the new
  `DFDataManager.get_spinup_warmup_steps()` and `DF_config.yaml` key. The FM/AF 2070
  continuation is unaffected (default 0).
- **DynamicStandardSim flux year labelling**: `_stock_to_flux()` now labels each flux row with
  the later (upper) stock row's year (`stock.loc[i]`), matching `cbm_scenario_fluxes()` and the
  main `DynamicScenarioGenerator`, so the series starts at `base_year + 1` with no
  calibration-year placeholder row.

### Removed
- **GeoGoblin / geo-runner support**: v0.6.0 targets GOBLIN_lite only. All `geo_*` runners,
  generators, and data-processing modules were removed. Fork the `0.5.0` line for GeoGoblin.
- **Legacy `Runner` / `DataManager` entry point** (`default_runner.runner.Runner`,
  `resource_manager.cbm_runner_data_manager.DataManager` as a public entry point): replaced by
  the scenario generators (`NationalScenarioGenerator`, `DynamicScenarioGenerator`,
  `StandardSimGenerator`, `DynamicStandardSimGenerator`).

### Notes
- **AIDB**: Irish CBM defaults now in `ireland_cbm_defaults_v6.1.db`. Both database filenames are
  naming conventions hard-coded in the loaders (`database_manager.py`, `loaders/base.py`,
  `paths.py`), independent of the package version.

---

## [0.5.0] - 2025-02-11 (Unreleased)

### Added
- **Support for Standing Forests**: New functionality to handle standing forest inventory data, enabling initialization with pre-existing StandAge and tracking disturbances over time.
- **Dynamic Initialization**:
  - `initialize_stands` now differentiates between afforestation (Classifier2 = "A") and standing forest (Classifier2 = "L"), applying appropriate rules and ensuring column consistency.
  - For afforestation, species transitions are applied using a transition dictionary.
- **Vectorized Disturbance Application**: Disturbances are now applied using precomputed rules for better performance across afforestation and standing forests.
- **Aggregated Disturbance Records**: Disturbance events are grouped by species, year, and disturbance type, reducing redundancy.
- **High and Low Intensity Management Options**: Added high and low intensity management options, set in the forest configuration file.
- **Context Managers for Input Parameters**: Input parameters are now passed via a context manager. There is a different context manager for the default runner and for the geo_runner.
- **Updated Examples and README**: All examples and the README have been updated to reflect the new changes.
- **Scenario Afforestation Delay**: Added functionality to set a delay for afforestation in the default runner. This delay can have an afforestation rate for a specified number of years, with the remaining afforestation area annualized evenly up to the target year.
- **Explicit Afforestation Dataframe**: Added the ability to generate an explicit afforestation dataframe for the default runner.

### Changed
- **Improved Performance**:
  - Eliminated unnecessary loops in `apply_disturbance`, replacing them with vectorized DataFrame operations, significantly reducing processing time.
  - Concatenation Safety Checks: Ensured safe concatenation of `disturbance_df` to prevent issues when DataFrames are empty or contain only NaN values.
- **Database Update**: Updated the database to `cbm_runner_0.4.3.db`, which includes the high and low intensity disturbances data tables.
- **Harvest Module**: Major changes in `harvest.py`, now based on pandas vectorization rather than a list of custom objects. The tracking bug was also solved here, stands are now split into a new stand and tracked separately from its original stand when a disturbance event takes place.

### Fixed
- **StandAge Initialization Issue**: Existing forest stands retain their correct age, avoiding incorrect initialization with StandAge = 0.
- **Resolved disturbance_dict Tuple Bug**: Fixed an issue where `disturbance_dict` was mistakenly passed as a tuple, causing failures during disturbance lookups.
- **Column Validation**: Ensured consistent presence of `Classifier1`, `Classifier2`, `Classifier4`, `Amount`, `StandAge`, and `LastDist` across all datasets.
- **Tracking Bug**: Stands are now split into a new stand and tracked separately from its original stand when a disturbance event takes place.

### Removed
- **Fire Disturbance**: Fire is not included at the moment.

### Notes
- **Disturbance Types**: DISTID1, DISTID2, and DISTID4 correspond to clearfell, thinning, and afforestation, respectively.