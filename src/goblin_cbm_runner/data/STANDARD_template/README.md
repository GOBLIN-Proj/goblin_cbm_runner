# Standard Runner Template

Minimal working example for `StandardRunner` (and the `StandardSimGenerator` /
`DynamicStandardSimGenerator` entry points). Copy this directory and replace the data
with your own forest stands.

## Usage

```python
from goblin_cbm_runner.runners.standard_runner import StandardRunner

runner = StandardRunner(
    csv_directory='./my_stands/',
    config={'baseline_year': 2020, 'end_year': 2050},
)
runner.generate_input_data()   # validates required files
results = runner.run_flux_scenarios()
```

See `tests/examples/standard_example.py` (and `standard_sim_example.py`,
`dynamic_standard_sim_example.py`) for runnable examples using this template.

---

## File Reference

### classifiers.csv

Defines classifier sets and their values.

| Column | Description |
|--------|-------------|
| `classifier_id` | Numeric ID of the classifier set |
| `name` | Value used in inventory, growth, events, transitions CSV files |
| `description` | Human-readable label; also used as the `user_species` key in sit_config.json |

Special row: `classifier_id=N, name=_CLASSIFIER, description=<classifier_name>` declares
a new classifier set named `<classifier_name>`.

### age_classes.csv

Defines age class bins.

| Column | Description |
|--------|-------------|
| `id` | Age class identifier (AGEID0, AGEID1, ...) |
| `size` | Width of age class in years (0 for the first class, 5 for subsequent) |

AGEID0 size=0 is required. The 21 entries here (AGEID0–AGEID20) cover ages 0–100 years
in 5-year steps, matching the 21 volume columns (Vol0–Vol20) in growth.csv.

### disturbance_types.csv

| Column | Description |
|--------|-------------|
| `id` | Disturbance type identifier (e.g. DISTID1) |
| `name` | Name referenced in events, transitions, inventory CSV files |

These names are also mapped to AIDB disturbance types in `sit_config.json`.

### inventory.csv

One row per forest stand.

| Column | Description |
|--------|-------------|
| `Classifier1..N` | Classifier values (matching `name` in classifiers.csv) |
| `UsingID` | TRUE/FALSE — whether age is specified by age class ID |
| `Age` | Stand age in years (used when UsingID=FALSE) |
| `Area` | Stand area in hectares |
| `Delay` | Regeneration delay in years (0 for established stands) |
| `UNFCCCL` | Land class: 0=Forest, 2=NonForest (pre-afforestation) |
| `HistDist` | Historic disturbance type (disturbance that created this stand cohort) |
| `LastDist` | Last disturbance type applied to this stand |

### disturbance_events.csv

Defines when and how much to disturb stands.

Key columns (many filter columns are set to -1 to disable):

| Column | Description |
|--------|-------------|
| `Classifier1..N` | Classifier filters (`?` = wildcard) |
| `SWStart/SWEnd` | Softwood age eligibility range (0–210 for no constraint) |
| `HWStart/HWEnd` | Hardwood age eligibility range |
| `Efficency` | Harvest efficiency (1 = 100%) |
| `Sort_Type` | Stand selection: 3=oldest SW first, 6=area-proportional |
| `Measurement_type` | M=Merchantable tC, A=Area (ha), P=Proportion |
| `Amount` | Target amount (units depend on Measurement_type) |
| `Dist_Type_ID` | Which disturbance type to apply |
| `Step` | Simulation timestep at which this event occurs |

### transitions.csv

Post-disturbance classifier transitions (e.g. regeneration species after clearcut).

Columns: pre-disturbance classifier filters + `Dist_Type_ID` + post-disturbance classifier
values + `RegenDelay`, `ResetAge`, `Percent`.

### growth.csv

Yield curves defining merchantable volume by age class.

| Column | Description |
|--------|-------------|
| `Classifier1..N` | Classifier values this curve applies to (`?` = wildcard) |
| `LeadSpecies` | Leading species (classifier value name) |
| `Vol0..Vol20` | Volume at each age class (m³/ha per 5-year age class, 21 values) |

### sit_config.json

Links all CSV files and maps user identifiers to AIDB identifiers.

Key sections:
- `import_config` — file paths for each SIT component
- `mapping_config.species` — maps species classifier values to AIDB species
- `mapping_config.disturbance_types` — maps disturbance names to AIDB disturbance types
- `mapping_config.spatial_units` — admin/eco boundary (Ireland/Ireland for Irish AIDB)

The `user_species` values in species mapping must match the `description` column in
classifiers.csv (e.g. `IE_Spruce13-16`).

---

## Adding More Species

1. Add rows to `classifiers.csv` (one per species):
   `1,MySpruce,IE_Spruce13-16`

2. Add corresponding species mapping to `sit_config.json`:
   `{"user_species": "IE_Spruce13-16", "default_species": "IE_Spruce13-16"}`

3. Add yield curve to `growth.csv`:
   `MySpruce,L,mineral,YC13_16,MySpruce,0,0.031,...`

4. Add inventory rows for the new species in `inventory.csv`

## Available AIDB Species (ireland_cbm_defaults_v6.1.db)

- IE_Pine4-12, IE_Pine13-30
- IE_Spruce4-12, IE_Spruce13-16, IE_Spruce17-20-thin, IE_Spruce17-20-nothin
- IE_Spruce21-24-thin, IE_Spruce21-24-nothin, IE_Spruce25-32-thin, IE_Spruce25-32-nothin
- IE_SGB, IE_FGB, IE_OC
- IE_Cbmix-Bl, IE_Cbmix-Conifer, IE_Cmix
- IE_SNFGB-peat, IE_SNFGB-mineral
