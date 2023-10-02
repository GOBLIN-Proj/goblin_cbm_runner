import pandas as pd
import os
from cbm_runner.harvest import Harvest


def main():
    path = "./data"
    config = os.path.join(path, "cbm_factory.yaml")

    harvest_class = Harvest(config)

    print(harvest_class.get_harvest_areas())


if __name__ == "__main__":
    main()
