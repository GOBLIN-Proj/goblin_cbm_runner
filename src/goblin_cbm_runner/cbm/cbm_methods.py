"""
============
CBM Methods
============
This module contains methods for running the Carbon Budget Model (CBM) and generating carbon stocks and fluxes for different scenarios.
"""
from libcbm.model.cbm import cbm_simulator
from libcbm.input.sit import sit_cbm_factory
from libcbm.model.cbm import cbm_variables
from libcbm.model.cbm.cbm_output import CBMOutput
from libcbm.storage.backends import BackendType
import pandas as pd
from goblin_cbm_runner.resource_manager.cbm_pools import Pools
from goblin_cbm_runner.resource_manager.flux_manager import FluxManager
from typing import Callable
from libcbm.storage.dataframe import DataFrame
from libcbm.model.cbm.cbm_variables import CBMVariables
from libcbm.model.cbm.cbm_model import CBM
from libcbm.input.sit.sit import SIT
from goblin_cbm_runner.cbm_validation.validation import ValidationData
import os



class CBMSim:
    """
    A class for running the Carbon Budget Model (CBM) and generating carbon stocks and fluxes for different scenarios.

    This class provides functionalities to run the CBM model and generate carbon stocks and fluxes for different scenarios. 
    The CBM model is a widely used model for estimating carbon stocks and fluxes in forest ecosystems. 
    The model uses input data and parameters to simulate the carbon dynamics in forest ecosystems over time.

    Methods:
        cbm_baseline_forest_stock(): Runs a baseline forest simulation using the CBM model.
        cbm_aggregate_scenario_stock(): Generate carbon stocks for the CBM (Carbon Budget Model) scenario data.
        libcbm_scenario_fluxes(): Generate carbon Fluxes using the Libcbm method for the CBM (Carbon Budget Model) scenario data.
        cbm_scenario_fluxes(): Calculate the carbon fluxes for each scenario in the given forest data.
        spinup(): Spin up the CBM model.
        step(): Step the CBM model forward one timestep.
        baseline_simulate_stock(): Runs a baseline (managed) forest simulation using the CBM model.
        cbm_basic_validation(): Generate carbon stocks for the CBM (Carbon Budget Model) scenario data.
        forest_raw_fluxes(): Calculate the carbon fluxes in the given forest data. The categories are not aggregated.
        cbm_baseline_summary_fluxes(): Calculate the carbon fluxes for baseline managed forest in the given forest data.
        

    Attributes:
        pools: An instance of the Pools class.
        Flux_class: An instance of the FluxManager class.
        AGB: A list of above-ground biomass pools.
        BGB: A list of below-ground biomass pools.
        deadwood: A list of deadwood pools.
        litter: A list of litter pools.
        soil: A list of soil organic matter pools.
    """
    def __init__(self):
        self.pools = Pools()
        self.Flux_class = FluxManager()
        self.AGB = self.pools.get_above_ground_biomass_pools()
        self.BGB = self.pools.get_below_ground_biomass_pools()
        self.deadwood = self.pools.get_deadwood_pools()
        self.litter = self.pools.get_litter_pools()
        self.soil = self.pools.get_soil_organic_matter_pools()


    def cbm_baseline_forest_stock(self, cbm_data_class, years, year_range, input_path, database_path):
            """
            Runs a baseline forest simulation using the CBM model.

            Returns:
                pandas.DataFrame: DataFrame containing the calculated managed forest stocks.
            """
            
            
            sit, classifiers, inventory = cbm_data_class.set_baseline_input_data_dir(
                input_path, database_path
            )

            cbm_output = CBMOutput(
                classifier_map=sit.classifier_value_names,
                disturbance_type_map=sit.disturbance_name_map)
            

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
                    reporting_func=cbm_output.append_simulation_result,
                    backend_type=BackendType.numpy
                )

            pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])


            annual_carbon_stocks = pd.DataFrame(
                {
                    "Year": pi["timestep"],
                    "AGB": pi[self.AGB].sum(axis=1),
                    "BGB": pi[self.BGB].sum(axis=1),
                    "Deadwood": pi[self.deadwood].sum(axis=1),
                    "Litter": pi[self.litter].sum(axis=1),
                    "Soil": pi[self.soil].sum(axis=1),
                    "Total Ecosystem": pi[self.AGB
                                          + self.BGB
                                          + self.deadwood
                                          + self.litter
                                          + self.soil].sum(axis=1),

                }
            )

            annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
                ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Total Ecosystem"]
            ].sum()

            annual_carbon_stocks["Year"] = year_range

            return annual_carbon_stocks  
    

    def cbm_aggregate_scenario_stock(self, sc, cbm_data_class, years, year_range, input_path, database_path):
        """
        Generate carbon stocks for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated stocks.
        """

        sit, classifiers, inventory = cbm_data_class.set_input_data_dir(sc, input_path, db_path=database_path)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

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
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])

       
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil", "Harvest","Total Ecosystem"]
        ].sum()

        annual_carbon_stocks["Year"] = year_range
        annual_carbon_stocks["Scenario"] = sc

        return annual_carbon_stocks
    

    def libcbm_scenario_fluxes(self, sc,  cbm_data_class, years, year_range, input_path, database_path):
        """
        Generate carbon Fluxes using the Libcbm method for the CBM (Carbon Budget Model) scenario data.

        Args:
            sc (str): The scenario name.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated fluxes.
        """

        sit, classifiers, inventory = cbm_data_class.set_input_data_dir(sc, input_path, db_path=database_path)


        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

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
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )
        flux = cbm_output.flux.to_pandas()
        state = cbm_output.state.to_pandas()
        parameters = cbm_output.parameters.to_pandas()
        area = cbm_output.area.to_pandas()

        #flux_dataframe 
        flux_dataframe= self.Flux_class.concatenated_fluxes_data(flux, state, parameters, area)#.groupby(["TimeStep"]).sum()

        flux_results = self.Flux_class.flux_filter_and_aggregate(flux_dataframe)
        flux_results["Scenario"] = sc
        flux_results["Year"] = year_range[:-1]


        annual_process_fluxes = pd.DataFrame(
            {
                "Scenario": sc,
                "Timestep":flux_results.index,
                "Year": year_range[:-1],
                "DeltaBIO": flux_results["DeltaBio"],
                "DeltaDOM": flux_results["DeltaDOM"],
                "Harvest": flux_results["Harvest"],
                "Total Ecosystem_delta": flux_results["Delta_Ecos"],

            }
        )

      

        return annual_process_fluxes
    

    def cbm_scenario_fluxes(self, forest_data):
        """
        Calculate the carbon fluxes for each scenario in the given forest data.

        Args:
            forest_data (pd.DataFrame): DataFrame containing forest data.

        Returns:
            pd.DataFrame: DataFrame containing the calculated fluxes.
        """
        fluxes = pd.DataFrame(columns=forest_data.columns)

        for i in forest_data.index[1:]:
            fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i-1, "Year"])
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
            fluxes.loc[i - 1, "Harvest"] = (
                forest_data.loc[i, "Harvest"] - forest_data.loc[i - 1, "Harvest"]
            )
            fluxes.loc[i - 1, "Total Ecosystem"] = (
                forest_data.loc[i, "Total Ecosystem"]
                - forest_data.loc[i - 1, "Total Ecosystem"]
            )

        return fluxes
    


    def spinup(self, sit: SIT,
                classifiers: DataFrame,
                inventory: DataFrame) -> CBMVariables:
        """
        Spin up the CBM model.
        
        Args:
            sit (SIT): The SIT object.
            classifiers (DataFrame): The classifiers.
            inventory (DataFrame): The inventory.
        """
        
        with sit_cbm_factory.initialize_cbm(sit) as cbm:

            cbm_vars = cbm_variables.initialize_simulation_variables(
                classifiers,
                inventory,
                cbm.pool_codes,
                cbm.flux_indicator_codes,
                inventory.backend_type,
            )

            spinup_vars = cbm_variables.initialize_spinup_variables(
                cbm_vars,
                inventory.backend_type,
                spinup_params=None, # if you are setting non-default mean annual temperature this may be important
                include_flux=False,
            )

            cbm.spinup(spinup_vars)

            if "mean_annual_temp" in spinup_vars.parameters.columns:
                # since the mean_annual_temp appears in the spinup parameters, carry
                # it forward to the simulation period so that we have consistent
                # columns in the outputs
                cbm_vars.parameters.add_column(
                    spinup_vars.parameters["mean_annual_temp"],
                    cbm_vars.parameters.n_cols,
                )
            cbm_vars = cbm.init(cbm_vars)

            return cbm_vars
        
        
    def step(self, time_step: int, sit: SIT, cbm_vars: CBMVariables) -> CBMVariables:
        """
        Step the CBM model forward one timestep.

        Args:
            time_step (int): The timestep.
            sit (SIT): The SIT object.
            cbm_vars (CBMVariables): The CBM variables.
        """
        with sit_cbm_factory.initialize_cbm(sit) as cbm:
            rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
            # apply rule based disturbances to the cbm_vars for this timestep
            cbm_vars = rule_based_processor.pre_dynamics_func(time_step, cbm_vars)
            # advance the C dynamics
            cbm_vars = cbm.step(cbm_vars)
            return cbm_vars
        


    def baseline_simulate_stock(self, cbm_data_class, years, year_range, input_path, database_path):
        """
        Runs a baseline (managed) forest simulation using the CBM model.

        Args:
            cbm_data_class (CBMData): The CBM data class object.
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path (str): The path to the input data.
            database_path (str): The path to the database.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated managed forest stocks.
        """
        spinup_sit, classifiers, inventory = cbm_data_class.set_spinup_baseline_input_data_dir(
            input_path, database_path
        )

        step_sit, redundant_classifier, redundant_inventory = cbm_data_class.set_baseline_input_data_dir(
            input_path, database_path
        )

        cbm_output = CBMOutput(
            classifier_map=spinup_sit.classifier_value_names)
            
        cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
        # append the t=0 (post-spinup results)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            # the t cbm_vars replace the t-1 cbm_vars
            cbm_vars = self.step(t, step_sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)


        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])

       
        annual_carbon_stocks = pd.DataFrame(
            {
                "Year": pi["timestep"],
                "AGB": pi[self.AGB].sum(axis=1),
                "BGB": pi[self.BGB].sum(axis=1),
                "Deadwood": pi[self.deadwood].sum(axis=1),
                "Litter": pi[self.litter].sum(axis=1),
                "Soil": pi[self.soil].sum(axis=1),
                "Harvest": pi["Products"],
                "Total Ecosystem": pi[self.AGB
                                      + self.BGB
                                      + self.deadwood
                                      + self.litter
                                      + self.soil].sum(axis=1),

            }
        )

        annual_carbon_stocks = annual_carbon_stocks.groupby(["Year"], as_index=False)[
            ["AGB", "BGB", "Deadwood", "Litter", "Soil","Harvest", "Total Ecosystem"]
        ].sum()

        annual_carbon_stocks["Year"] = year_range

        return annual_carbon_stocks
    

    def baseline_simulate_stock_raw_output(self, cbm_data_class, years, year_range, input_path, database_path):
        """
        Runs a baseline (managed) forest simulation using the CBM model.

        Args:
            cbm_data_class (CBMData): The CBM data class object.
            years (int): The number of years to simulate.
            year_range (list): The range of years to simulate.
            input_path (str): The path to the input data.
            database_path (str): The path to the database.

        Returns:
            pandas.DataFrame: DataFrame containing the calculated managed forest stocks.
        """
        spinup_sit, classifiers, inventory = cbm_data_class.set_spinup_baseline_input_data_dir(
            input_path, database_path
        )

        step_sit, redundant_classifier, redundant_inventory = cbm_data_class.set_baseline_input_data_dir(
            input_path, database_path
        )

        cbm_output = CBMOutput(
            classifier_map=spinup_sit.classifier_value_names)
            
        cbm_vars = self.spinup(spinup_sit, classifiers, inventory)
        # append the t=0 (post-spinup results)
        cbm_output.append_simulation_result(0, cbm_vars)

        for t in range(1, int(years) + 1):
            # the t cbm_vars replace the t-1 cbm_vars
            cbm_vars = self.step(t, step_sit, cbm_vars)
            cbm_output.append_simulation_result(t, cbm_vars)


        pi =  cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas(), left_on=["identifier", "timestep"], right_on=["identifier", "timestep"])


        return pi
    

    def cbm_basic_validation(self,years, input_path, database_path):
        """
        Generate validation data for the CBM model for a set of specified inputs. 

        Args:
            years (int): The number of years to simulate.
            input_path (str): The path to the SIT input data.
            database_path (str): The path to the database.
        
        Returns:
            dict: A dictionary containing the generated validation data.
        """
        sit_config_path = os.path.join(input_path, "sit_config.json")

        sit = sit_cbm_factory.load_sit(sit_config_path, database_path)

        classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)

        cbm_output = CBMOutput(
            classifier_map=sit.classifier_value_names,
            disturbance_type_map=sit.disturbance_name_map)

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
                reporting_func=cbm_output.append_simulation_result,
                backend_type=BackendType.numpy
            )

        si =  cbm_output.state.to_pandas()
        pools = cbm_output.pools.to_pandas()
        flux = cbm_output.flux.to_pandas()
        parameters = cbm_output.parameters.to_pandas()
        area = cbm_output.area.to_pandas()

        state_by_timestep = ValidationData.gen_disturbance_statistics(rule_based_processor, years)

        events = ValidationData.gen_sit_events(rule_based_processor)

        linked_events = ValidationData.merge_events(events, state_by_timestep)

        results= {
            "data_area":area,
            "data_flux":flux,
            "data_params":parameters,
            "data_pools":pools,
            "data_state":si,
            "linked_events":linked_events}
    
        return results
    

    def forest_raw_fluxes(self, forest_data):
        """
        Calculate the carbon fluxes in the given forest data. The categories are not aggregated.

        Args:
            forest_data (pd.DataFrame): DataFrame containing forest data.

        Returns:
            pd.DataFrame: DataFrame containing the calculated fluxes.
        """
        fluxes = pd.DataFrame(columns=forest_data.columns)

        columns = ["SoftwoodMerch", 
                   "SoftwoodFoliage", 
                   "SoftwoodOther", 
                   "SoftwoodCoarseRoots", 
                   "SoftwoodFineRoots", 
                   "HardwoodMerch", 
                   "HardwoodFoliage", 
                   "HardwoodOther", 
                   "HardwoodCoarseRoots", 
                   "HardwoodFineRoots", 
                   "AboveGroundVeryFastSoil", 
                   "BelowGroundVeryFastSoil", 
                   "AboveGroundFastSoil", 
                   "BelowGroundFastSoil", 
                   "MediumSoil", 
                   "AboveGroundSlowSoil", 
                   "BelowGroundSlowSoil", 
                   "SoftwoodStemSnag", 
                   "SoftwoodBranchSnag", 
                   "HardwoodStemSnag", 
                   "HardwoodBranchSnag", 
                   "CO2", 
                   "CH4", 
                   "CO", 
                   "NO2", 
                   "Products"]
        
        for i in forest_data.index:

            if i > 0:
                for col in forest_data.columns:
                    if col not in columns:
                        fluxes.loc[i, col] = forest_data.loc[i, col]
                        
                fluxes.loc[i - 1, "timestep"] = int(forest_data.loc[i, "timestep"]) -1
                for column in columns:
                    fluxes.loc[i - 1, column] = (
                        forest_data.loc[i, column] - forest_data.loc[i - 1, column]
                    )
            else:
                fluxes.loc[i , "timestep"] = int(forest_data.loc[i, "timestep"])
                for column in columns:
                    fluxes.loc[i, column] = forest_data.loc[i, column]

        return fluxes
    

    def cbm_baseline_summary_fluxes(self, forest_data):
        """
        Calculate the carbon fluxes for baseline managed forest in the given forest data.

        Args:
            forest_data (pd.DataFrame): DataFrame containing forest data.

        Returns:
            pd.DataFrame: DataFrame containing the calculated fluxes.
        """
        fluxes = pd.DataFrame(columns=forest_data.columns)

        for i in forest_data.index[1:]:
            fluxes.loc[i - 1, "Year"] = int(forest_data.loc[i-1, "Year"])
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
            fluxes.loc[i - 1, "Harvest"] = (
                forest_data.loc[i, "Harvest"] - forest_data.loc[i - 1, "Harvest"]
            )
            fluxes.loc[i - 1, "Total Ecosystem"] = (
                forest_data.loc[i, "Total Ecosystem"]
                - forest_data.loc[i - 1, "Total Ecosystem"]
            )

        return fluxes