import cbm_runner.generated_input_data as input_data_path
import cbm_runner.baseline_input_conf as baseline_conf_path
from cbm_runner.cbm_data_factory import DataFactory
from cbm_runner.cbm_runner_data_manager import DataManager
from cbm_runner.cbm_pools import Pools

from libcbm.model.cbm import cbm_simulator
from libcbm.input.sit import sit_cbm_factory

import pandas as pd


class Runner:
    def __init__(
        self,
        config_path,
        calibration_year,
        forest_end_year,
        afforest_data,
        scenario_data,
    ):
        self.path = input_data_path.get_local_dir()
        self.baseline_conf_path = baseline_conf_path.get_local_dir()
        self.cbm_data_class = DataFactory(
            config_path, calibration_year, forest_end_year, afforest_data, scenario_data
        )
        self.data_manager_class = DataManager(calibration_year, config_path)

        self.INDEX = [int(i) for i in afforest_data.scenario.unique()]
        self.forest_end_year = forest_end_year
        
        self.pools = Pools()
        self.AGB = self.pools.get_above_ground_biomass_pools()
        self.BGB = self.pools.get_below_ground_biomass_pools()
        self.deadwood = self.pools.get_deadwood_pools()
        self.litter = self.pools.get_litter_pools()
        self.soil = self.pools.get_soil_organic_matter_pools()
        self.flux_pools = self.pools.get_annual_process_fluxes()

        self.generate_base_input_data()
        self.forest_baseline_dataframe = self.cbm_baseline_forest()
        self.forest_baseline_dataframe["Stock"].to_csv("forest_basline.csv")


    def generate_base_input_data(self):
        path = self.baseline_conf_path

        self.cbm_data_class.clean_baseline_data_dir(path)

        self.cbm_data_class.make_classifiers(None, path)
        self.cbm_data_class.make_config_json(None, path)
        self.cbm_data_class.make_age_classes(None, path)
        self.cbm_data_class.make_yield_curves(None, path)
        self.cbm_data_class.make_inventory(None, path)
        self.cbm_data_class.make_disturbance_events(None, path)
        self.cbm_data_class.make_disturbance_type(None, path)
        self.cbm_data_class.make_transition_rules(None, path)

    def generate_input_data(self):
        path = self.path

        self.cbm_data_class.clean_data_dir(path)
        self.cbm_data_class.make_data_dirs(self.INDEX, path)

        for i in self.INDEX:
            self.cbm_data_class.make_classifiers(i, path)
            self.cbm_data_class.make_config_json(i, path)
            self.cbm_data_class.make_age_classes(i, path)
            self.cbm_data_class.make_yield_curves(i, path)
            self.cbm_data_class.make_inventory(i, path)
            self.cbm_data_class.make_disturbance_events(i, path)
            self.cbm_data_class.make_disturbance_type(i, path)
            self.cbm_data_class.make_transition_rules(i, path)

    def run_aggregate_scenarios(self):
        forest_data = pd.DataFrame()
        aggregate_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.cbm_aggregate_scenario(i)["Stock"]

            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe["Stock"],
                on="Year",
                how="inner",
                suffixes=("", "_baseline"),
            )

            # Add the values for selected columns where 'year' matches
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
            for col in columns_to_add:
                merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]

            # Drop the duplicate columns (columns with '_baseline' suffix)
            merged_data.drop(
                columns=[col + "_baseline" for col in columns_to_add], inplace=True
            )

            # Update the original 'forest_data' DataFrame with the merged and added data
            forest_data = merged_data

            forest_data_copy = forest_data.copy(deep=True)

            aggregate_forest_data = pd.concat(
                [aggregate_forest_data, forest_data_copy], ignore_index=True
            )

        return aggregate_forest_data

    def run_flux_scenarios(self):
        forest_data = pd.DataFrame()
        fluxes_data = pd.DataFrame()
        fluxes_forest_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.cbm_aggregate_scenario(i)["Stock"]

            forest_data.to_csv("forest_data.csv")

            # Assuming 'year' is the common column
            merged_data = pd.merge(
                forest_data,
                self.forest_baseline_dataframe["Stock"],
                on="Year",
                how="inner",
                suffixes=("", "_baseline"),
            )

            # Add the values for selected columns where 'year' matches
            columns_to_add = ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
            for col in columns_to_add:
                merged_data[col] = merged_data[col] + merged_data[col + "_baseline"]

            # Drop the duplicate columns (columns with '_baseline' suffix)
            merged_data.drop(
                columns=[col + "_baseline" for col in columns_to_add], inplace=True
            )

            # Update the original 'forest_data' DataFrame with the merged and added data
            forest_data = merged_data

            fluxes_data = self.cbm_scenario_fluxes(forest_data)

            fluxes_forest_data = pd.concat(
                [fluxes_forest_data, fluxes_data], ignore_index=True
            )

        return fluxes_forest_data

    def afforestation_scenarios_structure(self):
        forest_data = pd.DataFrame()
        structure_data = pd.DataFrame()

        for i in self.INDEX:
            forest_data = self.cbm_aggregate_scenario(i)["Structure"]
            forest_data["Scenario"] = i

            structure_data = pd.concat([structure_data, forest_data], ignore_index=True)

        return structure_data

    def cbm_baseline_forest(self):
        forest_baseline_year = self.data_manager_class.get_forest_baseline_year()
        forestry_end_year = self.forest_end_year
        path = self.baseline_conf_path

        years = forestry_end_year - forest_baseline_year

        year_range = [
            year + 1 for year in range(forest_baseline_year -1, forestry_end_year)
        ]


        sit, classifiers, inventory = self.cbm_data_class.set_baseline_input_data_dir(
            path
        )

        classifier_config = sit_cbm_factory.get_classifiers(
            sit.sit_data.classifiers, sit.sit_data.classifier_values
        )

        results, reporting_func = cbm_simulator.create_in_memory_reporting_func(
            classifier_map={
                x["id"]: x["value"] for x in classifier_config["classifier_values"]
            }
        )

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=reporting_func,
            )

        pi = results.pools.merge(results.classifiers)


        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1) *-1,
                "BGB": pi[self.BGB].sum(axis=1) *-1,
                "Deadwood": pi[self.deadwood].sum(axis=1) *-1,
                "Litter": pi[self.litter].sum(axis=1) *-1,
                "Soil": pi[self.soil].sum(axis=1) *-1,
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1) *-1,

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
        ].sum()

        annual_carbon_stocks["Year"] = year_range

        age = results.state.merge(results.classifiers)[
            ["age", "time_since_last_disturbance", "last_disturbance_type"]
        ]
        area = results.area.merge(results.classifiers)

        structure_df = pd.concat([age, area], axis=1)

        return {"Stock": annual_carbon_stocks, "Structure": structure_df, "Raw": pi}

    def cbm_aggregate_scenario(self, sc):
        forest_baseline_year = self.data_manager_class.get_afforestation_baseline()
        forestry_end_year = self.forest_end_year
        path = self.path

        years = forestry_end_year - forest_baseline_year

        year_range = [
            year + 1 for year in range(forest_baseline_year - 1, forestry_end_year)
        ]

        sit, classifiers, inventory = self.cbm_data_class.set_input_data_dir(sc, path)

        classifier_config = sit_cbm_factory.get_classifiers(
            sit.sit_data.classifiers, sit.sit_data.classifier_values
        )

        results, reporting_func = cbm_simulator.create_in_memory_reporting_func(
            classifier_map={
                x["id"]: x["value"] for x in classifier_config["classifier_values"]
            }
        )

        # Simulation
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            # Create a function to apply rule based disturbance events and transition rules based on the SIT input
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(
                sit, cbm
            )
            # The following line of code spins up the CBM inventory and runs it through 200 timesteps.
            cbm_simulator.simulate(
                cbm,
                n_steps=years,
                classifiers=classifiers,
                inventory=inventory,
                pre_dynamics_func=rule_based_processor.pre_dynamics_func,
                reporting_func=reporting_func,
            )

        pi = results.pools.merge(results.classifiers)
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1) *-1,
                "BGB": pi[self.BGB].sum(axis=1) *-1,
                "Deadwood": pi[self.deadwood].sum(axis=1) *-1,
                "Litter": pi[self.litter].sum(axis=1) *-1,
                "Soil": pi[self.soil].sum(axis=1) *-1,
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1) *-1,

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
        ].sum()

        annual_carbon_stocks["Year"] = year_range
        annual_carbon_stocks["Scenario"] = sc

        age = results.state.merge(results.classifiers)[
            ["age", "time_since_last_disturbance", "last_disturbance_type"]
        ]
        area = results.area.merge(results.classifiers)

        structure_df = pd.concat([age, area], axis=1)

        return {"Stock": annual_carbon_stocks, "Structure": structure_df, "Raw": pi}

    def cbm_scenario_fluxes(self, forest_data):
        fluxes = pd.DataFrame(columns=forest_data.columns)

        for i in forest_data.index:
            if i > 0:
                fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i, "Year"])
                fluxes.loc[i - 1, "Scenario"] = int(forest_data.loc[i, "Scenario"])
                fluxes.loc[i - 1, "AGB"] = (
                    forest_data.loc[i, "AGB"] - forest_data.loc[i - 1, "AGB"]
                )
                fluxes.loc[i - 1, "BGB"] = (
                    forest_data.loc[i, "BGB"] - forest_data.loc[i - 1, "BGB"]
                )
                fluxes.loc[i - 1, "Deadwood"] = (
                    forest_data.loc[i, "Deadwood"] - forest_data.loc[i - 1, "Deadwood"]
                )
                fluxes.loc[i - 1, "Litter"] = (
                    forest_data.loc[i, "Litter"] - forest_data.loc[i - 1, "Litter"]
                )
                fluxes.loc[i - 1, "Soil"] = (
                    forest_data.loc[i, "Soil"] - forest_data.loc[i - 1, "Soil"]
                )
                fluxes.loc[i - 1, "Total Ecosystem"] = (
                    forest_data.loc[i, "Total Ecosystem"]
                    - forest_data.loc[i - 1, "Total Ecosystem"]
                )


        return fluxes
