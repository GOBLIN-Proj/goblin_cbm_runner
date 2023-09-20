import pandas as pd 
import os
from cbm_runner.cbm_data_factory import DataFactory
from cbm_runner.yield_curves import YieldCurves
from cbm_runner.inventory import Inventory
from cbm_runner.disturbances import Distrubances
def main():

    path = "./data"

    afforest_data = pd.read_csv(os.path.join(path, "scenario_afforestation.csv"), index_col=0)
    
    config = os.path.join(path, "cbm_factory.yaml")

    sc_data = pd.read_csv(os.path.join(path, "scenario_dataframe.csv"))

    calibration_year = 2020
    forest_end_year = 2050

    #cbm_data_class = DataFactory(config,calibration_year, forest_end_year, afforest_data, sc_data)

    #print(cbm_data_class.afforestation_data)
    
    disturbance_class = Distrubances(config,calibration_year, forest_end_year, afforest_data, sc_data)

    print(disturbance_class.fill_baseline_forest())
    #cbm_data_class.make_classifiers(0, path)
    #cbm_data_class.make_config_json(0, path)
    #cbm_data_class.make_age_classes(0, path)
    #cbm_data_class.make_yield_curves(0, path)
    #cbm_data_class.make_inventory(0, path)
    #cbm_data_class.make_disturbance_events(0, path)
    #cbm_data_class.make_disturbance_type(0, path)
    #cbm_data_class.make_transition_rules(0, path)

    #disturbance_class = Distrubances(sc_data, afforest_data, calibration_year, config)

    #disturbance_class.fill_legacy_data().to_csv("./data/disturbance_test.csv")


    #inventory_class = Inventory(config, sc_data)

    #print(inventory_class.legacy_forest_inventory())

    #inventory_df = inventory_class.make_inventory_structure(0, path)

    #print(inventory_class.inventory_iterator(inventory_df))

    #print(inventory_class.afforestation_inventory(0,inventory_df))

    #inventory_class.afforestation_inventory(0,inventory_df).to_csv("./data/afforestation.csv")

    #print(inventory_class.legacy_afforestation_peat_soils())


if __name__ == "__main__":
    main()

