from goblin_cbm_runner.cbm_validation.validation_runner import ValRunner
from pathlib import Path
import os 
import warnings



def main():

    warnings.filterwarnings("ignore")

    path = Path("./data/FM_data/")
    results_path = Path("./data/FM_results/")
    start = 1990
    end = 2030
    
    # Iterate over all files in the directory
    for filename in os.listdir(results_path):
        # Construct the full file path
        file_path = os.path.join(results_path, filename)
        
        # Check if it's a file (to avoid directories, though it's assumed there are only CSV files)
        if os.path.isfile(file_path):
            try:
                # Delete the file
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    


    name = "fm_scenario_"

    runner_class = ValRunner(start, end, path, None)

    forest_data = runner_class.run_FM_validation()

    for key, value in forest_data.items():
        if value is not None:
           file_name = f"{name}{key}_forest_gross_raw.csv"
           value.to_csv(results_path / file_name)


if __name__ == "__main__":
    main()