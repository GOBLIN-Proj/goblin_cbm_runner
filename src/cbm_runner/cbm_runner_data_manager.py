import yaml
import cbm_runner.parser as parser
import pandas as pd


class DataManager:
    def __init__(self, config_file=None, scenario_data=None):
        self.config_data = self.get_config_data(config_file) if config_file else None

        self.forest_baseline_year = 1990
        self.afforestation_baseline = 1990

        self.non_forest_dict = {
            "Sitka": {"mineral": "NFSitka_mineral", "peat": "NFSitka_peat"},
            "Pine": {"mineral": "NFPine_mineral", "peat": "NFPine_peat"},
            "SGB": {"mineral": "NFSGB_mineral", "peat": "NFSGB_peat"},
            "FGB": {"mineral": "NFFGB_mineral", "peat": "NFFGB_peat"},
            "OC": {"mineral": "NFOC_mineral", "peat": "NFOC_peat"},
            "CBmix": {"mineral": "NFCBmix_mineral", "peat": "NFCBmix_peat"},
        }

        self.non_forest_soils = {
            "mineral": [
                "NFSitka_mineral",
                "NFPine_mineral",
                "NFSGB_mineral",
                "NFFGB_mineral",
                "NFOC_mineral",
                "NFCBmix_mineral",
            ],
            "peat": [
                "NFSitka_peat",
                "NFPine_peat",
                "NFSGB_peat",
                "NFFGB_peat",
                "NFOC_peat",
                "NFCBmix_peat",
                "NFCBmix_peat",
            ],
        }

        self.forest_type_keys = {"afforestation": "A", "legacy": "L"}

        self.soils_dict = {
            "mineral": [
                "Cambisols (Ireland)",
                "Gleysols (Ireland)",
                "Luvisols (Ireland)",
                "Podzolic (Ireland)",
            ],
            "peat": ["Peat (Ireland)"],
        }

        self.classifiers = {
            "Baseline": {
                "Species": {
                    "Pine": "Other pine",
                    "Sitka": "Sitka spruce",
                    "SGB": "Slow Growing Unspecified broadleaved species - Genus type",
                    "FGB": "Fast Growing Unspecified broadleaved species - Genus type",
                    "CBmix": "Mix Spruce",
                    "OC": "Other Spruce",
                },
                "Forest type": {"L": "Legacy"},
                "Soil classes": {"mineral": "Mineral", "peat": "Peat"},
                "Yield classes": {
                    "YC6": "Yield class 6",
                    "YC10": "Yield class 10",
                    "YC12_20": "Yield class 12 to 20",
                    "YC4_12": "Yield class 4 to 12",
                    "YC13_16": "Yield class 13 to 16",
                    "YC17_20": "Yield class 17 to 20",
                    "YC20_24": "Yield class 20 to 24",
                    "YC24_30": "Yield class 24 to 30",
                },
            },
            "Scenario": {
                "Species": {
                    "Pine": "Other pine",
                    "Sitka": "Sitka spruce",
                    "SGB": "Slow Growing Unspecified broadleaved species - Genus type",
                    "FGB": "Fast Growing Unspecified broadleaved species - Genus type",
                    "CBmix": "Mix Spruce",
                    "OC": "Other Spruce",
                    "NFPine_mineral": "NonForestPineMineral",
                    "NFSitka_mineral": "NonForestSitkaMineral",
                    "NFSGB_mineral": "NonForestSGBMineral",
                    "NFFGB_mineral": "NonForestFGBMineral",
                    "NFCBmix_mineral": "NonForestCBmixMineral",
                    "NFOC_mineral": "NonForestOCMineral",
                    "NFPine_peat": "NonForestPinePeat",
                    "NFSitka_peat": "NonForestSitkaPeat",
                    "NFSGB_peat": "NonForestSGBPeat",
                    "NFFGB_peat": "NonForestFGBPeat",
                    "NFCBmix_peat": "NonForestCBmixPeat",
                    "NFOC_peat": "NonForestOCPeat",
                },
                "Forest type": {"A": "Afforestation", "L": "Legacy"},
                "Soil classes": {"mineral": "Mineral", "peat": "Peat"},
                "Yield classes": {
                    "YC6": "Yield class 6",
                    "YC10": "Yield class 10",
                    "YC12_20": "Yield class 12 to 20",
                    "YC4_12": "Yield class 4 to 12",
                    "YC13_16": "Yield class 13 to 16",
                    "YC17_20": "Yield class 17 to 20",
                    "YC20_24": "Yield class 20 to 24",
                    "YC24_30": "Yield class 24 to 30",
                },
            },
        }

        self.disturbances_config = {
            "Baseline": ["DISTID1", "DISTID2", "DISTID3", "DISTID5"],
            "Scenario": ["DISTID1", "DISTID2", "DISTID3", "DISTID4", "DISTID5"],
        }

        self.disturbance_dict = (
            {
                "DISTID1": {
                    "Sitka": parser.get_clearfell_baseline(self.config_data),
                    "SGB": 0,
                },
                "DISTID2": {
                    "Sitka": parser.get_thinning_baseline(self.config_data),
                    "SGB": 0,
                },
            }
            if config_file
            else None
        )

        self.forest_baseline_disturbance_dict = {
            "DISTID1": {
                "Sitka": {
                    "Spruce_13_16": 50,
                    "Spruce_17_20": 50,
                    "Spruce_20_24": 31,
                    "Spruce_24_30": 31,
                }
            },
            "DISTID2": {"Sitka": {"YC10": None, "YC16": None, "YC20": 0, "YC24": 0}},
        }

        self.yield_name_dict = {
            "Sitka": {
                "YC4_12": "Spruce_4_12",
                "YC13_16": "Spruce_13_16",
                "YC17_20": "Spruce_17_20",
                "YC20_24": "Spruce_20_24",
                "YC24_30": "Spruce_24_30",
            },
            "Pine": {"YC12_20": "Pine_4_12", "YC12_20": "Pine_12_20"},
            "SGB": {"YC6": "SGB"},
            "FGB": {"YC6": "FGB"},
            "OC": {"YC10": "OC", "YC10": "OC"},
            "CBmix": {"YC10": "CBmix"},
        }

        self.species_name_dict = {
            "Spruce_4_12": {"YC4_12": "Sitka"},
            "Spruce_13_16": {"YC13_16": "Sitka"},
            "Spruce_17_20": {"YC17_20": "Sitka"},
            "Spruce_20_24": {"YC20_24": "Sitka"},
            "Spruce_24_30": {"YC24_30": "Sitka"},
            "Pine_12_20": {"YC12_20": "Pine"},
            "Pine_4_12": {"YC12_20": "Pine"},
            "SGB": {"YC6": "SGB"},
            "FGB": {"YC6": "FGB"},
            "OC": {"YC10": "OC"},
            "CBmix": {"YC10": "CBmix"},
            "Cmix": {"YC10": "OC"},
        }

        self.afforestation_yield_name_dict = {
            "NFPine_mineral": "YC12_20",
            "NFSitka_mineral": ["YC4_12", "YC13_16", "YC17_20", "YC20_24", "YC24_30"],
            "NFSGB_mineral": "YC6",
            "NFFGB_mineral": "YC6",
            "NFCBmix_mineral": "YC10",
            "NFOC_mineral": "YC10",
            "NFPine_peat": "YC12_20",
            "NFSitka_peat": ["YC4_12", "YC13_16", "YC17_20", "YC20_24", "YC24_30"],
            "NFSGB_peat": "YC6",
            "NFFGB_peat": "YC6",
            "NFCBmix_peat": "YC10",
            "NFOC_peat": "YC10",
        }

        self.yield_basline_dict = {
            "Sitka": {
                "YC13_16": 0.37,
                "YC17_20": 0.26,
                "YC20_24": 0.20,
                "YC24_30": 0.17,
            },
            "Pine": {"YC12_20": 1},
            "SGB": {"YC6": 1},
            "FGB": {"YC6": 1},
            "OC": {"YC10": 1},
            "CBmix": {"YC10": 1},
        }

        self.scenario_data = (
            scenario_data if scenario_data is not None else pd.DataFrame()
        )

        self.scenario_disturbance_dict = (
            self.gen_scenario_disturbance_dict(scenario_data)
            if not self.scenario_data.empty
            else None
        )

        self.mapping = {
            "species": {
                "Pine": {"user_species": "Other pine", "default_species": "Other pine"},
                "Sitka": {
                    "user_species": "Sitka spruce",
                    "default_species": "Sitka spruce",
                },
                "SGB": {
                    "user_species": "Slow Growing Unspecified broadleaved species - Genus type",
                    "default_species": "Unspecified broadleaved species - Genus type",
                },
                "FGB": {
                    "user_species": "Fast Growing Unspecified broadleaved species - Genus type",
                    "default_species": "Unspecified broadleaved species - Genus type",
                },
                "CBmix": {"user_species": "Mix Spruce", "default_species": "Spruce"},
                "OC": {"user_species": "Other Spruce", "default_species": "Spruce"},
                "NFPine_mineral": {
                    "user_species": "NonForestPineMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFSitka_mineral": {
                    "user_species": "NonForestSitkaMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFSGB_mineral": {
                    "user_species": "NonForestSGBMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFFGB_mineral": {
                    "user_species": "NonForestFGBMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFCBmix_mineral": {
                    "user_species": "NonForestCBmixMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFOC_mineral": {
                    "user_species": "NonForestOCMineral",
                    "default_species": "Missing value - Genus type",
                },
                "NFPine_peat": {
                    "user_species": "NonForestPinePeat",
                    "default_species": "Missing value - Genus type",
                },
                "NFSitka_peat": {
                    "user_species": "NonForestSitkaPeat",
                    "default_species": "Missing value - Genus type",
                },
                "NFSGB_peat": {
                    "user_species": "NonForestSGBPeat",
                    "default_species": "Missing value - Genus type",
                },
                "NFFGB_peat": {
                    "user_species": "NonForestFGBPeat",
                    "default_species": "Missing value - Genus type",
                },
                "NFCBmix_peat": {
                    "user_species": "NonForestCBmixPeat",
                    "default_species": "Missing value - Genus type",
                },
                "NFOC_peat": {
                    "user_species": "NonForestOCPeat",
                    "default_species": "Missing value - Genus type",
                },
            },
            "boundary": "Ireland",
            "disturbance_types": {
                "DISTID1": {
                    "user_dist_type": "Clearcut",
                    "default_dist_type": "Clearcut harvesting with salvage",
                },
                "DISTID2": {
                    "user_dist_type": "Thinning",
                    "default_dist_type": "15% commercial thinning",
                },
                "DISTID3": {"user_dist_type": "Fire", "default_dist_type": "Wildfire"},
                "DISTID4": {
                    "user_dist_type": "Afforestation",
                    "default_dist_type": "Afforestation",
                },
                "DISTID5": {
                    "user_dist_type": "Unknown",
                    "default_dist_type": "Unknown",
                },
            },
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

        self.static_disturbance_cols = [
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
            "before_cols": [
                "Classifier1",
                "Classifier2",
                "Classifier3",
                "Classifier4",
                "UsingID",
                "SWStart",
                "SWEnd",
                "HWDStart",
                "HWEnd",
                "DistType",
            ],
            "after_cols": [
                "Classifier1",
                "Classifier2",
                "Classifier3",
                "Classifier4",
                "RegenDelay",
                "ResetAge",
                "Percent",
            ],
        }

    def get_config_data(self, config_file):
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)

        return config_data

    def gen_scenario_disturbance_dict(self, scenario_data):
        grouped_data = scenario_data.drop_duplicates(
            subset=["Scenarios", "Conifer harvest", "Conifer thinned"]
        ).reset_index(drop=True)

        scenario_disturbance_dict = {}

        for sc in grouped_data.Scenarios:
            scenario = sc
            mask = grouped_data.Scenarios == sc

            scenario_disturbance_dict[scenario] = {}
            scenario_disturbance_dict[scenario]["DISTID1"] = {}
            scenario_disturbance_dict[scenario]["DISTID2"] = {}

            scenario_disturbance_dict[scenario]["DISTID1"]["Sitka"] = grouped_data.loc[
                mask, "Conifer harvest"
            ].item()
            scenario_disturbance_dict[scenario]["DISTID1"]["SGB"] = 0

            scenario_disturbance_dict[scenario]["DISTID2"]["Sitka"] = grouped_data.loc[
                mask, "Conifer thinned"
            ].item()
            scenario_disturbance_dict[scenario]["DISTID2"]["SGB"] = 0

        return scenario_disturbance_dict
