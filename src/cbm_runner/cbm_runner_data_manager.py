import yaml
import cbm_runner.parser as parser
import pandas as pd

class DataManager:
    def __init__(self, config_file = None, scenario_data = None):

        self.forest_baseline_year = 1970
        self.afforestation_baseline = 1990

        self.species_proportions = { "CF": 0.90,
                                    "BL": 0.10}

        self.config_data = self.get_config_data(config_file) if config_file else None

        self.disturbance_dict = {
            "DISTID1":{"CF": parser.get_clearfell_baseline(self.config_data["Classifiers"]),
                       "BL":0},
            "DISTID2":{"CF": parser.get_thinning_baseline(self.config_data["Classifiers"]),
                       "BL":0}       
        } if config_file else None

        self.forest_baseline_disturbance_dict = {
            "DISTID1": {
                "CF": {
                    "Spruce_13_16": 50,
                    "Spruce_17_20": 50,
                    "Spruce_20_24": 31,
                    "Spruce_24_30": 31
                }
            },
            "DISTID2": {
                "CF": {
                    "YC10": None,
                    "YC16": None,
                    "YC20": 0,
                    "YC24": 0
                }
            }
        }

        self.scenario_data = scenario_data if scenario_data is not None else pd.DataFrame()

        self.scenario_disturbance_dict = self.gen_scenario_disturbance_dict(scenario_data) if not self.scenario_data.empty else None


        self.disturbance_age_dict = {
            "DISTID1":{"CF": {"YC10":{"sw_age_min":50,
                                      "sw_age_max":50,
                                      "hw_age_min":50,
                                      "hw_age_max":50},
                            "YC16":{"sw_age_min":50,
                                      "sw_age_max":50,
                                      "hw_age_min":50,
                                      "hw_age_max":50},
                            "YC20":{"sw_age_min":31,
                                      "sw_age_max":31,
                                      "hw_age_min":31,
                                      "hw_age_max":31},
                            "YC24":{"sw_age_min":31,
                                      "sw_age_max":31,
                                      "hw_age_min":31,
                                      "hw_age_max":31}},

                       "BL":{"YC10":{"sw_age_min":65,
                                      "sw_age_max":65,
                                      "hw_age_min":65,
                                      "hw_age_max":65},
                            "YC16":{"sw_age_min":65,
                                      "sw_age_max":65,
                                      "hw_age_min":65,
                                      "hw_age_max":65},
                            "YC20":{"sw_age_min":65,
                                      "sw_age_max":65,
                                      "hw_age_min":65,
                                      "hw_age_max":65},
                            "YC24":{"sw_age_min":65,
                                      "sw_age_max":65,
                                      "hw_age_min":65,
                                      "hw_age_max":65}}
                                      },
            "DISTID2":{"CF": {"YC10":{"sw_age_min":22,
                                      "sw_age_max":22,
                                      "hw_age_min":22,
                                      "hw_age_max":22},
                            "YC16":{"sw_age_min":22,
                                      "sw_age_max":22,
                                      "hw_age_min":22,
                                      "hw_age_max":22},
                            "YC20":{"sw_age_min":20,
                                      "sw_age_max":20,
                                      "hw_age_min":20,
                                      "hw_age_max":20},
                            "YC24":{"sw_age_min":22,
                                      "sw_age_max":22,
                                      "hw_age_min":22,
                                      "hw_age_max":22}},
                                      
                       "BL":{"YC10":{"sw_age_min":15,
                                      "sw_age_max":15,
                                      "hw_age_min":15,
                                      "hw_age_max":15},
                            "YC16":{"sw_age_min":15,
                                      "sw_age_max":15,
                                      "hw_age_min":15,
                                      "hw_age_max":15},
                            "YC20":{"sw_age_min":15,
                                      "sw_age_max":15,
                                      "hw_age_min":15,
                                      "hw_age_max":15},
                            "YC24":{"sw_age_min":15,
                                      "sw_age_max":15,
                                      "hw_age_min":15,
                                      "hw_age_max":15}}
                                      },
            "DISTID4":{"CF": {"YC10":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC16":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC20":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC24":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0}},
                                      
                       "BL":{"YC10":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC16":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC20":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0},
                            "YC24":{"sw_age_min":0,
                                      "sw_age_max":0,
                                      "hw_age_min":0,
                                      "hw_age_max":0}}
                                      }      
        }
        
        self.mapping = {
            "species": {
                "MF": {"user_species": "Mixedwood", "default_species": "Mixedwood"},
                "CF": {"user_species": "Sitka spruce", "default_species": "Sitka spruce"},
                "BL": {"user_species": "Sycamore", "default_species": "Sycamore"},
            },

            "boundary": "Ireland",

            "disturbance_types": {

                "DISTID1": {
                    "user_dist_type": "Clearcut",
                    "default_dist_type": "Clearcut harvesting with salvage"
                },
                "DISTID2": {
                        "user_dist_type": "Thinning",
                        "default_dist_type": "25% commercial thinning",
                    },
                "DISTID3": {"user_dist_type": "Fire", 
                            "default_dist_type": "Wildfire"},
                "DISTID4": {
                        "user_dist_type": "Afforestation",
                        "default_dist_type": "Afforestation",
                    },
                "DISTID5": {
                        "user_dist_type": "Unknown",
                        "default_dist_type": "Unknown",
                    },
            }
        }

        self.yield_name_dict = {
            "CF": {
                "YC10": "Spruce_13_16",
                "YC16": "Spruce_17_20",
                "YC20": "Spruce_20_24",
                "YC24": "Spruce_24_30",
            },
            "BL": "SGB",
            "MF": "CB_mix",
        }

        self.disturbance_cols = [
                "Classifier1",
                "Classifier2",
                "Classifier3",
                "Classifier4",
                "UsingID",
                "sw_age_min",
                "sw_age_max",
                "hw_age_min",
                "hw_age_max",
                "MinYearsSinceDist",
                "MaxYearsSinceDist",
                "LastDistTypeID",
                "MinTotBiomassC",
                "MaxTotBiomassC",
                "MinSWMerchBiomassC",
                "MaxSWMerchBiomassC",
                "MinHWMerchBiomassC",
                "MaxHWMerchBiomassC",
                "MinTotalStemSnagC",
                "MaxTotalStemSnagC",
                "MinSWStemSnagC",
                "MaxSWStemSnagC",
                "MinHWStemSnagC",
                "MaxHWStemSnagC",
                "MinTotalStemSnagMerchC",
                "MaxTotalStemSnagMerchC",
                "MinSWMerchStemSnagC",
                "MaxSWMerchStemSnagC",
                "MinHWMerchStemSnagC",
                "MaxHWMerchStemSnagC",
                "Efficiency",
                "SortType",
                "MeasureType",
                "Amount",
                "DistTypeID",
                "Year",
            ]
        
        self.static_disturbance_cols =[
                "MinYearsSinceDist",
                "MaxYearsSinceDist",
                "LastDistTypeID",
                "MinTotBiomassC",
                "MaxTotBiomassC",
                "MinSWMerchBiomassC",
                "MaxSWMerchBiomassC",
                "MinHWMerchBiomassC",
                "MaxHWMerchBiomassC",
                "MinTotalStemSnagC",
                "MaxTotalStemSnagC",
                "MinSWStemSnagC",
                "MaxSWStemSnagC",
                "MinHWStemSnagC",
                "MaxHWStemSnagC",
                "MinTotalStemSnagMerchC",
                "MaxTotalStemSnagMerchC",
                "MinSWMerchStemSnagC",
                "MaxSWMerchStemSnagC",
                "MinHWMerchStemSnagC",
                "MaxHWMerchStemSnagC",
            ]
     
        self.transition_cols = {
            "before_cols":["Classifier1",
                            "Classifier2",
                            "Classifier3",
                            "Classifier4",
                            "UsingID",
                            "SWStart",
                            "SWEnd",
                            "HWDStart",
                            "HWEnd",
                            "DistType",],
                            
            "after_cols":["Classifier1",
                            "Classifier2",
                            "Classifier3",
                            "Classifier4",
                            "RegenDelay",
                            "ResetAge",
                            "Percent",]
        }

    def get_config_data(self, config_file):
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)

        return config_data
    

    def gen_scenario_disturbance_dict(self, scenario_data):

        grouped_data = scenario_data.drop_duplicates(subset=["Scenarios", "Conifer harvest", "Conifer thinned"]).reset_index(drop=True)

        scenario_disturbance_dict = {}

        for sc in grouped_data.Scenarios:
            
            scenario = sc
            mask = (grouped_data.Scenarios == sc)

            scenario_disturbance_dict[scenario] = {} 
            scenario_disturbance_dict[scenario]["DISTID1"] = {}
            scenario_disturbance_dict[scenario]["DISTID2"] = {}

            scenario_disturbance_dict[scenario]["DISTID1"]["CF"] = grouped_data.loc[mask, "Conifer harvest"].item()
            scenario_disturbance_dict[scenario]["DISTID1"]["BL"] = 0 

            scenario_disturbance_dict[scenario]["DISTID2"]["CF"] = grouped_data.loc[mask, "Conifer thinned"].item()
            scenario_disturbance_dict[scenario]["DISTID2"]["BL"] = 0 

        return scenario_disturbance_dict
    


