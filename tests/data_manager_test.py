from cbm_runner.resource_manager.cbm_runner_data_manager import DataManager

def main():
    data_manager = DataManager()
    print(data_manager.get_non_forest_dict())
    print(data_manager.get_non_forest_soils())
    print(data_manager.get_forest_type_keys())
    print(data_manager.get_soils_dict())
    print(data_manager.get_classifiers())
    print(data_manager.get_disturbances_config())
    print(data_manager.get_yield_name_dict())
    print(data_manager.get_species_name_dict())
    print(data_manager.get_afforestation_yield_name_dict())
    print(data_manager.get_yield_basline_dict())
    print(data_manager.get_disturbance_cols())
    print(data_manager.get_static_disturbance_cols())
    print(data_manager.get_transition_cols())
    print(data_manager.get_mapping())
    print("##############################################")
    print(data_manager.get_disturbances_config())

if __name__ == "__main__":
    main()