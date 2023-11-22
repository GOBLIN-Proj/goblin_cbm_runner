# 🌲 CBM_runner, a CBM CFS3 interface for the GOBLIN model
[![license](https://img.shields.io/badge/License-MIT-red)](https://github.com/colmduff/goblin_lite/blob/0.1.0/LICENSE)
[![python](https://img.shields.io/badge/python-3.9-blue?logo=python&logoColor=white)](https://github.com/colmduff/cbm_runner)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

 Based on the [GOBLIN](https://gmd.copernicus.org/articles/15/2239/2022/) (**G**eneral **O**verview for a **B**ackcasting approach of **L**ivestock **IN**tensification) LifeCycle Analysis tool, the cbm_runner package generates the data requried for the CBM CFS3 (libcbm_py) tool. It also interfaces with the tool directly, generating results in a single dataframe for all scenarios. 

 The outputs are related to biomass, and dead organic matter. These are totaled into a total ecosystem value. 

 The estimated volumns are all in t of C. 



## Installation

Install from git hub. 

When prompted enter your ```<username>``` and password, which is your ```<access_token>```.

```<access_token>``` is provided by the repo manager.

```<username>``` pass your own github username.


```bash
pip install "cbm_runner@git+https://github.com/colmduff/cbm_runner.git@main" 

```

## Usage

The Runner class takes the total afforestation area and divides it evenly across years (calibration year - target year). 

```python
from cbm_runner.runner import Runner
import pandas as pd 
import os 

def main():
    #path to data
    path = "./data"

    #afforestation data for each scenario
    afforest_data = pd.read_csv(os.path.join(path, "scenario_afforestation.csv"), index_col=0)
    
    #basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    #scenario_data 
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    #calibration and end point
    calibration_year = 2020
    forest_end_year = 2050
    
    #instance of the Runner class
    runner = Runner(config,calibration_year, forest_end_year, afforest_data, sc_data)
    
    #generation of data for each of the scenarios
    runner.generate_input_data()

    #generation of aggregated results 
    runner.run_aggregate_scenarios().to_csv(os.path.join(path, "c_aggregate.csv"))

    #generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(path, "c_flux.csv"))


if __name__ == "__main__":
    main()
    
```
The ForestSimRunner class allows the user to specify annual afforestation rates in a seperate file. 

```python
from cbm_runner.forestsim_runner import ForestSimRunner
import pandas as pd
import os


def main():
    # path to data
    path = "./data"

    # afforestation data for each scenario
    afforest_data = pd.read_csv(
        os.path.join(path, "scenario_afforestation.csv"), index_col=0
    )

    afforest_data_annual = pd.read_csv(
        os.path.join(path, "scenario_afforestation_annual.csv"), index_col=0
    )

    # basic configuration file
    config = os.path.join(path, "cbm_factory.yaml")

    # scenario_data
    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    # calibration and end point
    calibration_year = 2020
    forest_end_year = 2050

    # instance of the Runner class
    runner = ForestSimRunner(config, calibration_year, forest_end_year, afforest_data, afforest_data_annual, sc_data)

    # generation of data for each of the scenarios
    runner.generate_input_data()

    # generation of aggregated results
    runner.run_aggregate_scenarios().to_csv(os.path.join(path, "forsim_c_aggregate.csv"))

    # generation of annual flux results
    runner.run_flux_scenarios().to_csv(os.path.join(path, "forsim_c_flux.csv"))


if __name__ == "__main__":
    main()
```
## License
This project is licensed under the terms of the MIT license.