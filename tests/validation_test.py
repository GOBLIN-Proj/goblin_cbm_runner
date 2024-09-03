from goblin_cbm_runner.cbm_validation.validation_runner import ValRunner

def main():
    path = "./data/validation_data/"
    results_path = "./data/validation_results/"
    start = 1990
    end = 2099
    val = ValRunner(start, end, path, None)

    data = val.run_validation()


    for key, value in data.items():
        if value is not None:
           value.to_csv(results_path + key + ".csv")

    df = val.run_scenario_disturbance_area_validation()
    
    df["merge_disturbances_and_parse"].to_csv(results_path + "merge_parse.csv")
    df["summary_disturbances"].to_csv(results_path + "dist_sum.csv")

    for key, value in data.items():
        if key == "primary_data":
            value.to_csv(results_path + key + ".csv")
            primary_data = value

    agg_flux = val.run_flux_validation_agg(primary_data)

    agg_flux.to_csv(results_path + "agg_flux.csv")



if __name__ == "__main__":
    main()