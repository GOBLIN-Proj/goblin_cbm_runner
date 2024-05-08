from cbm_runner.cbm_validation.validation_runner import ValRunner

def main():
    path = "./data/validation_data/"
    start = 1990
    end = 2050
    val = ValRunner(start, end, path, None)

    print(val.run_validation())

if __name__ == "__main__":
    main()