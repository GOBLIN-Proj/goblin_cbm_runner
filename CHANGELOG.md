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