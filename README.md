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

## Usage

The Runner class takes the total afforestation area and divides it evenly across years (calibration year - target year). 

```python
from goblin_cbm_runner.default_runner.runner import Runner
from goblin_cbm_runner.resource_manager.cbm_runner_data_manager import DataManager
import pandas as pd
import os


def main():
    # path to data
    path = "./data/runner_input"
    results_path = "./data/runner_results"

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "cbm_afforestation.csv"), index_col=0
    )

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020

    # instance of the DataManager class
    data_manager = DataManager(calibration_year = calibration_year,
                            config_file_path=config,
                            scenario_data=sc_data,
                            afforest_data=afforest_data)
    
    # instance of the Runner class
    runner = Runner(data_manager)

    # afforeation data
    runner.get_afforestation_dataframe().to_csv(os.path.join(results_path, "c_afforestation.csv"))

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(results_path, "c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(results_path, "c_flux.csv"))


if __name__ == "__main__":
    main()

```

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