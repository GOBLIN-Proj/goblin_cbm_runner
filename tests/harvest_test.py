import pandas as pd
import os
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker
import unittest


class TestAfforestationTracker(unittest.TestCase):
    def test_afforestation_and_harvest(self):
        tracker = AfforestationTracker()

        yield_class = "YC20_24"
        species = "Sitka"
        area = 100
        soil = "peat"

        proportion ={"DISTID1":0.1, "DISTID2":0.2}

        years = range(0, 40)
        # Afforestation data
        time = 2020
        for age in years:
            if age < 2:
                tracker.afforest(area, species, yield_class, soil)
            tracker.move_to_next_age()
            tracker.forest_disturbance(time, species, yield_class, soil, proportion)

            time += 1

 
        stand_data = tracker.get_stand_data_for_year()

        dict_age = tracker.get_stand_data_by_age()
        #print(stand_data)
        print("#######################")
        dist = tracker.get_disturbance_data_for_year()
        ic(dist)


        #for stand in tracker.disturbed_stands:
            #ic(stand.species)


if __name__ == '__main__':
    unittest.main()

