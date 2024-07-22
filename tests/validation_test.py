from goblin_cbm_runner.cbm_validation.validation_runner import ValRunner

def main():
    path = "./data/validation_data/"
    results_path = "./data/validation_results/"
    start = 1990
    end = 2050
    val = ValRunner(start, end, path, None)

    data = val.run_validation()

    for key, value in data.items():
        value.to_csv(results_path + key + ".csv")

    val.run_flux_validation(data["data_pools"]).to_csv(results_path + "fluxes.csv")

if __name__ == "__main__":
    main()