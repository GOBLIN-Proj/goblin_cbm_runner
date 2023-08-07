import yaml
import cbm_runner.parser as parser
import pandas as pd

class DataManager:
    def __init__(self, config_file = None, scenario_data = None):

        self.forest_baseline_year = 1991

        self.species_proportions = { "CF": 0.65,
                                    "BL": 0.35}

        self.config_data = self.get_config_data(config_file) if config_file else None

        self.disturbance_dict = {
            "DISTID1":{"CF": parser.get_clearfell_baseline(self.config_data["Classifiers"]),
                       "BL":0},
            "DISTID2":{"CF": parser.get_thinning_baseline(self.config_data["Classifiers"]),
                       "BL":0}       
        } if config_file else None

        self.scenario_data = scenario_data if scenario_data is not None else pd.DataFrame()

        self.scenario_disturbance_dict = self.gen_scenario_disturbance_dict(scenario_data) if not self.scenario_data.empty else None


        self.disturbance_age_dict = {
            "DISTID1":{"CF": {"YC10":{"sw_age_min":"AGEID5",
                                      "sw_age_max":"AGEID5",
                                      "hw_age_min":"AGEID5",
                                      "hw_age_max":"AGEID5"},
                            "YC16":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC20":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC24":{"sw_age_min":"AGEID3",
                                      "sw_age_max":"AGEID3",
                                      "hw_age_min":"AGEID3",
                                      "hw_age_max":"AGEID3"}},

                       "BL":{"YC10":{"sw_age_min":"AGEID5",
                                      "sw_age_max":"AGEID5",
                                      "hw_age_min":"AGEID5",
                                      "hw_age_max":"AGEID5"},
                            "YC16":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC20":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC24":{"sw_age_min":"AGEID3",
                                      "sw_age_max":"AGEID3",
                                      "hw_age_min":"AGEID3",
                                      "hw_age_max":"AGEID3"}}
                                      },
            "DISTID2":{"CF": {"YC10":{"sw_age_min":"AGEID5",
                                      "sw_age_max":"AGEID5",
                                      "hw_age_min":"AGEID5",
                                      "hw_age_max":"AGEID5"},
                            "YC16":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC20":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC24":{"sw_age_min":"AGEID3",
                                      "sw_age_max":"AGEID3",
                                      "hw_age_min":"AGEID3",
                                      "hw_age_max":"AGEID3"}},
                                      
                       "BL":{"YC10":{"sw_age_min":"AGEID5",
                                      "sw_age_max":"AGEID5",
                                      "hw_age_min":"AGEID5",
                                      "hw_age_max":"AGEID5"},
                            "YC16":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC20":{"sw_age_min":"AGEID4",
                                      "sw_age_max":"AGEID4",
                                      "hw_age_min":"AGEID4",
                                      "hw_age_max":"AGEID4"},
                            "YC24":{"sw_age_min":"AGEID3",
                                      "sw_age_max":"AGEID3",
                                      "hw_age_min":"AGEID3",
                                      "hw_age_max":"AGEID3"}}
                                      },
            "DISTID4":{"CF": {"YC10":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC16":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC20":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC24":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"}},
                                      
                       "BL":{"YC10":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC16":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC20":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"},
                            "YC24":{"sw_age_min":"AGEID0",
                                      "sw_age_max":"AGEID0",
                                      "hw_age_min":"AGEID0",
                                      "hw_age_max":"AGEID0"}}
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
            }
        }

        self.yield_name_dict = {
            "CF": {
                "YC10": "Spruce_4_12",
                "YC16": "Spruce_13_16",
                "YC20": "Spruce_17_20",
                "YC24": "Spruce_20_24",
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
    


