# 🌲 GOBLIN_CBM_runner, a CBM CFS3 interface for the GOBLIN model
[![license](https://img.shields.io/badge/License-MIT-red)](https://github.com/GOBLIN-Proj/goblin_lite/blob/0.1.0/LICENSE)
[![python](https://img.shields.io/badge/python-3.9-blue?logo=python&logoColor=white)](https://github.com/GOBLIN-Proj/cbm_runner)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

 Based on the [GOBLIN](https://gmd.copernicus.org/articles/15/2239/2022/) (**G**eneral **O**verview for a **B**ackcasting approach of **L**ivestock **IN**tensification) LifeCycle Analysis tool, the cbm_runner package generates the data requried for the CBM CFS3 (libcbm_py) tool. It also interfaces with the tool directly, generating results in a single dataframe for all scenarios. 

 The outputs are related to biomass, and dead organic matter. These are summed into a total ecosystem value. 

 The estimated volumns are all in t of C. 



## Installation

Install from git hub. 

```bash
pip install "goblin_cbm_runner@git+https://github.com/GOBLIN-Proj/goblin_cbm_runner.git@main" 

```

Install from PyPI

```bash
pip install goblin_cbm_runner
```

> **v0.6.0 note:** From v0.6.0 the package targets **GOBLIN_lite only** — GeoGoblin / geo-runner
> support was removed (fork the `0.5.0` line if you need it). The old `Runner` / `DataManager`
> entry point has been replaced by the scenario generators below. Output is **archive-only**:
> call `export_archive()` to write a self-describing SQLite `.db`; no CSVs are written automatically.

## Usage

There are four entry points. All accept a scenario DataFrame and produce an annual carbon-flux
DataFrame plus a SQLite archive.

### National pipeline — `NationalScenarioGenerator`

The standard national simulation (Forest Management + Afforestation + Scenarios) using the
bundled Irish database, to 2070.

```python
from goblin_cbm_runner.scenario_generator import NationalScenarioGenerator

nsg = NationalScenarioGenerator(
    scenario_data=scenario_df,          # pandas DataFrame of scenarios
    afforestation_data=afforest_df,     # pandas DataFrame of afforestation areas
    config={"afforest_delay": 5, "annual_rate_pre_delay": 1200},
    comprehensive=False,                # True to also capture pools/flux/state validation tables
)

results = nsg.run_flux_simulation()     # annual flux DataFrame (all scenarios + baseline)
nsg.export_archive("./simulation_archive.db")
```

### Dynamic pipeline — `DynamicScenarioGenerator`

Extends FM and AF beyond 2070 with **NAI-based (Net Annual Increment) harvest**, and extends the
scenario end year to match.

```python
from goblin_cbm_runner.dynamic_scenario_generator import DynamicScenarioGenerator

dsg = DynamicScenarioGenerator(
    scenario_data=scenario_df,
    afforestation_data=afforest_df,
    config={"afforest_delay": 5, "annual_rate_pre_delay": 1200},
    dynamic_config={"harvest_ratio": 0.75, "dynamic_years": 50},  # optional; 0.75 recommended
)

results = dsg.run_flux_simulation()            # extended FM + AF + SC
baseline = dsg.run_baseline_flux_simulation()  # extended FM + AF only
dsg.export_archive("./dynamic_archive.db")
```

### Standard pipeline (user CSVs) — `StandardSimGenerator`

Run a simulation from your **own inventory CSV files** with an explicit disturbance schedule — no
internal database of stands required (the bundled AIDB is still used for CBM parameters).

```python
from goblin_cbm_runner.standard_sim_generator import StandardSimGenerator

# Copy and edit the template CSVs first:
StandardSimGenerator.get_template("./my_forest/")

gen = StandardSimGenerator(
    csv_directory="./my_forest/",
    config={"baseline_year": 2020, "end_year": 2050},
    scenario=0,
)
results = gen.run_flux_simulation()
gen.export_archive("./standard_archive.db")
```

### Dynamic standard pipeline (user CSVs + NAI) — `DynamicStandardSimGenerator`

Your own inventory CSVs with **NAI-based dynamic harvest**. Omit `end_year` for "NAI from day 1",
or set it for a static warm-up period before the dynamic phase.

```python
from goblin_cbm_runner.dynamic_standard_sim_generator import DynamicStandardSimGenerator

gen = DynamicStandardSimGenerator(
    csv_directory="./my_forest/",
    config={"baseline_year": 2020},                              # omit end_year → years=0
    dynamic_config={"harvest_ratio": 0.75, "dynamic_years": 30},
)
results = gen.run_flux_simulation()
gen.export_archive("./dynamic_standard_archive.db")
```

Runnable versions of all four live in [`tests/examples/`](tests/examples/)
(`nsg_example.py`, `dsg_example.py`, `standard_sim_example.py`, `dynamic_standard_sim_example.py`).

## CBM Disturbance Sort Types Note

`libcbm_py` is not a direct conversion of the CBM-CFS3 model, and there are some small differences.  

One key difference is the **available sort types for stand disturbances**. Some sorting options in CBM-CFS3 are **not available** in `libcbm_py`, while others may function slightly differently.  

In particular, the **"Sort by time since softwood component was last harvested" (4)** and **"Sort by time since hardwood component was last harvested" (13)** are missing from `libcbm_py`. These sorts help prioritize stands based on past harvests, which can be important for disturbance modeling.  

Below, we provide the **full set of sort types from CBM-CFS3**, followed by the **available sorts in `libcbm_py`**, along with suggested approximations for missing sorts.

---

### **Sort Types from CBM-CFS3**
The following table lists all disturbance sort types available in CBM-CFS3:

| Sort Type | Description |
|-----------|------------|
| **1**  | No sorting; a proportion of each record to disturb is calculated. Only applicable to disturbance events with proportion (`P`) targets. |
| **2**  | Sort by merchantable biomass carbon (highest first). Only applicable to disturbance events with merchantable carbon (`M`) targets. |
| **3**  | Sort by oldest softwood first. |
| **4**  | Sort by time since the softwood component was last harvested. |
| **5**  | Sort by SVO (State Variable Object) ID. Used for spatially explicit projects and instructs the model to disturb 100% of a single eligible record. |
| **6**  | Sort randomly. Only applicable to fire and insect disturbance events. |
| **7**  | Sort by total stem snag carbon (highest first). |
| **8**  | Sort by softwood stem snag carbon (highest first). |
| **9**  | Sort by hardwood stem snag carbon (highest first). |
| **10** | Sort by softwood merchantable carbon (highest first). |
| **11** | Sort by hardwood merchantable carbon (highest first). |
| **12** | Sort by oldest hardwood first. |
| **13** | Sort by time since the hardwood component was last harvested. |

---

### **Available Sort Types in `libcbm_py`**
Below are the disturbance sort types that are implemented in `libcbm_py`:

```python
{
    1: "PROPORTION_OF_EVERY_RECORD",
    2: "MERCHCSORT_TOTAL",
    3: "SORT_BY_SW_AGE",
    5: "SVOID",
    6: "RANDOMSORT",
    7: "TOTALSTEMSNAG",
    8: "SWSTEMSNAG",
    9: "HWSTEMSNAG",
    10: "MERCHCSORT_SW",
    11: "MERCHCSORT_HW",
    12: "SORT_BY_HW_AGE",
}
```


## License
This project is licensed under the terms of the MIT license.