"""
Flux Manager
============
This module provides tools for scaling, filtering, and transforming carbon flux data 
within the context of a Carbon Budget Model (CBM). It integrates with the CBMpools class
to generate disturbance fluxes and process fluxes while ensuring consistency across data.
"""

from goblin_cbm_runner.resource_manager.cbm_pools import Pools
import pandas as pd 


class FluxManager:
    """
    Manages the preparation and transformation of carbon flux data for use in a Carbon Budget Model.

    Responsibilities:
        * **Initialization:** Establishes a link to a `Pools` object (from CBMpools module) to access carbon pool definitions.
        * **Scaling:** Scales flux data based on a given area (`scale_flux_data`).
        * **Filtering:** Removes rows in flux data where all flux values are zero (`filter_flux_data`).
        * **Result Generation:** Combines scaled and filtered flux data with area and disturbance information (`flux_results_dataframes`).
        * **Flux Creation:** Generates disturbance, total litter, gross growth, and process fluxes for a CBM model (`create_disturbance_fluxes`, `create_total_litter`, `create_gross_growthAG`, `create_gross_growthBG`, `create_process_fluxes`).
    """
    def __init__(self):
        self.CBMpools = Pools()

    def scale_flux_data(self, flux_data, area):
        """
        Scales relevant carbon flux columns in a DataFrame based on a provided area. 

        Args:
            flux_data (pandas.DataFrame):  DataFrame containing unscaled carbon flux data.
            area (float or numeric column): The area value to be used as a scaling factor.

        Returns:
            pandas.DataFrame: A DataFrame with updated flux values scaled by the area.
        """
        columns =['identifier', 'timestep', 'land_class', 'disturbance_type']

        # Identify columns to scale
        columns_to_scale = [col for col in flux_data.columns if col not in columns]
        flux_data.to_csv("flux_data_test_before.csv")
        # Scale only rows where 'target_type' == 'Area'
        for col in columns_to_scale:
            flux_data[col] = flux_data[col] * area["area"]
        
        return flux_data

        
    def filter_flux_data(self, flux_data):
        """
        Removes rows from a flux DataFrame where all valid flux values are zero.

        Filtering eliminates time steps where no carbon movement is happening.

        Args:
            flux_data (pandas.DataFrame): DataFrame containing carbon flux data.

        Returns:
            pandas.DataFrame: Filtered DataFrame with only rows containing non-zero flux values.
        """
        
        valid_columns = flux_data.columns.drop(['identifier', 'timestep', 'land_class', 'disturbance_type'])

        # Calculate the sum across rows for valid columns and create a boolean mask
        mask = flux_data[valid_columns].sum(axis=1) != 0

        # Apply the mask to filter rows, keeping all columns
        flux_filtered = flux_data[mask]

        return flux_filtered
    

    def flux_results_dataframes(self, flux, state, parameters, area):
        """
        Combines scaled and filtered carbon flux data.

        Args:
            object:  An object holding flux data, area, and state information.

        Returns:
            pandas.DataFrame: DataFrame with augmented flux data ready for CBM use.
        """
        flux = self._add_identifier(flux, state, parameters)

        #scaled_data = self.scale_flux_data(flux, area)
        
        output = self.filter_flux_data(flux)
       
        return output


    def _add_identifier(self, flux, state, parameters):
        """
        Adds land class and disturbance type columns to an existing flux DataFrame.

        Args:
            object: An object holding flux data, land class, and disturbance type information.

        Returns:
            pandas.DataFrame: Flux DataFrame with 'land_class' and 'disturbance_type' columns added.   
        """        

        flux['land_class'] = state['land_class'].values
        flux['disturbance_type'] = parameters['disturbance_type'].values

        return flux


    def create_disturbance_fluxes(self,flux, state, parameters, area):
        """
        Creates a DataFrame of carbon fluxes related to disturbances. 

        Args:
            object: An object holding flux data, area, and state information.

        Returns:
            pandas.DataFrame: A DataFrame containing calculated disturbance fluxes.
        """ 
        dist_flux = self.flux_results_dataframes(flux, state, parameters, area)

        dist_cols = self.CBMpools.get_disturbance_flux_columns()

        dist_dict = dict.fromkeys(dist_cols, 0.0)

        total_litter_disturbance = dist_flux[[
            "DisturbanceMerchLitterInput",
            "DisturbanceFolLitterInput",
            "DisturbanceOthLitterInput",
            "DisturbanceCoarseLitterInput",
            "DisturbanceFineLitterInput",]].sum(axis=1)
        
        dist_dict["TimeStep"] = dist_flux["timestep"]
        dist_dict["LandClassID"] = dist_flux["land_class"]
        dist_dict["CO2Production"] = dist_flux["DisturbanceCO2Production"]
        dist_dict["CH4Production"] = dist_flux["DisturbanceCH4Production"]
        dist_dict["COProduction"] = dist_flux["DisturbanceCOProduction"]
        dist_dict["BioCO2Emission"] = dist_flux["DisturbanceBioCO2Emission"]
        dist_dict["BioCH4Emission"] = dist_flux["DisturbanceBioCH4Emission"]
        dist_dict["BioCOEmission"] = dist_flux["DisturbanceBioCOEmission"]
        dist_dict["DOMCO2Emission"] = dist_flux["DisturbanceDOMCO2Emission"]
        dist_dict["DOMCH4Emssion"] = dist_flux["DisturbanceDOMCH4Emission"]
        dist_dict["DOMCOEmission"] = dist_flux["DisturbanceDOMCOEmission"]
        dist_dict["SoftProduction"] = dist_flux["DisturbanceSoftProduction"]
        dist_dict["HardProduction"] = dist_flux["DisturbanceHardProduction"]
        dist_dict["DOMProduction"] = dist_flux["DisturbanceDOMProduction"]
        dist_dict["BiomassToSoil"] = total_litter_disturbance
        dist_dict["MerchLitterInput"] = dist_flux["DisturbanceMerchLitterInput"]
        dist_dict["FolLitterInput"] = dist_flux["DisturbanceFolLitterInput"]
        dist_dict["OthLitterInput"] = dist_flux["DisturbanceOthLitterInput"]
        dist_dict["CoarseLitterInput"] = dist_flux["DisturbanceCoarseLitterInput"]
        dist_dict["FineLitterInput"] = dist_flux["DisturbanceFineLitterInput"]
        dist_dict["VFastAGToAir"] = dist_flux["DisturbanceVFastAGToAir"]
        dist_dict["VFastBGToAir"] = dist_flux["DisturbanceVFastBGToAir"]
        dist_dict["FastAGToAir"] = dist_flux["DisturbanceFastAGToAir"]
        dist_dict["FastBGToAir"] = dist_flux["DisturbanceFastBGToAir"]
        dist_dict["MediumToAir"] = dist_flux["DisturbanceMediumToAir"]
        dist_dict["SlowAGToAir"] = dist_flux["DisturbanceSlowAGToAir"]
        dist_dict["SlowBGToAir"] = dist_flux["DisturbanceSlowBGToAir"]
        dist_dict["SWStemSnagToAir"] = dist_flux["DisturbanceSWStemSnagToAir"]
        dist_dict["SWBranchSnagToAir"] = dist_flux["DisturbanceSWBranchSnagToAir"]
        dist_dict["HWStemSnagToAir"] = dist_flux["DisturbanceHWStemSnagToAir"]
        dist_dict["HWBranchSnagToAir"] = dist_flux["DisturbanceHWBranchSnagToAir"]
        dist_dict["MerchToAir"] = dist_flux["DisturbanceMerchToAir"]
        dist_dict["FolToAir"] = dist_flux["DisturbanceFolToAir"]
        dist_dict["OthToAir"] = dist_flux["DisturbanceOthToAir"]
        dist_dict["CoarseToAir"] = dist_flux["DisturbanceCoarseToAir"]
        dist_dict["FineToAir"] = dist_flux["DisturbanceFineToAir"]

        return pd.DataFrame(dist_dict)
    

    def create_total_litter(self, flux):
        """
        Calculates the total litter production based on relevant litter flux columns.

        Args:
            object: An object holding flux data and other relevant state information.

        Returns:
             pandas.Series: A Series representing the total litter production.
        """
        total_litter = flux[self.CBMpools.get_total_litter()].sum(axis=1)

        return total_litter
    
    def create_gross_growthAG(self, flux):
        """
        Calculates the gross growth for aboveground biomass.

        Args:
            object: An object holding flux data and other relevant state information.

        Returns:
            pandas.Series: A Series representing the calculated aboveground gross growth.
        """
        
        gross_growth = flux["DeltaBiomass_AG"]+ flux[self.CBMpools.get_gross_growth_AG()].sum(axis=1)

        return gross_growth
    
    def create_gross_growthBG(self, flux):
        """
        Calculates the gross growth for belowground biomass.

        Args:
            object: An object holding flux data and other relevant state information.

        Returns:
            pandas.Series: A Series representing the calculated belowground gross growth.
        """            
        gross_growth = flux["DeltaBiomass_BG"]+flux[self.CBMpools.get_gross_growth_BG()].sum(axis=1)

        return gross_growth
    
    def create_process_fluxes(self, flux, state, parameters):
        """
        Creates a DataFrame of annual process fluxes in the CBM.

        Args:
            object: An object holding flux data, area, and state information.

        Returns:
            pandas.DataFrame:  DataFrame with calculated annual process fluxes.        
        """
        process_flux = self._add_identifier(flux, state, parameters)
        total_litter = self.create_total_litter(flux)
        gross_growthAG = self.create_gross_growthAG(flux)
        gross_growthBG = self.create_gross_growthBG(flux)

        process_cols = self.CBMpools.get_annual_process_columns()

        process_dict = dict.fromkeys(process_cols, 0.0)

        process_dict["TimeStep"] = process_flux["timestep"]
        process_dict["LandClassID"] = process_flux["land_class"]
        process_dict["DOMCO2Emission"] = process_flux["DecayDOMCO2Emission"]
        process_dict["DeltaBiomass_AG"] = process_flux["DeltaBiomass_AG"]
        process_dict["DeltaBiomass_BG"] = process_flux["DeltaBiomass_BG"]
        process_dict["DeltaDOM"] = total_litter - process_flux["DecayDOMCO2Emission"]
        process_dict["BiomassToSoil"] = total_litter
        process_dict["MerchLitterInput"] = process_flux["TurnoverMerchLitterInput"]
        process_dict["FolLitterInput"] = process_flux["TurnoverFolLitterInput"]
        process_dict["OthLitterInput"] = process_flux["TurnoverOthLitterInput"]
        process_dict["CoarseLitterInput"] = process_flux["TurnoverCoarseLitterInput"]
        process_dict["FineLitterInput"] = process_flux["TurnoverFineLitterInput"]
        process_dict["VFastAGToAir"] = process_flux["DecayVFastAGToAir"]
        process_dict["VFastBGToAir"] = process_flux["DecayVFastBGToAir"]
        process_dict["FastAGToAir"] = process_flux["DecayFastAGToAir"]
        process_dict["FastBGToAir"] = process_flux["DecayFastBGToAir"]
        process_dict["MediumToAir"] = process_flux["DecayMediumToAir"]
        process_dict["SlowAGToAir"] = process_flux["DecaySlowAGToAir"]
        process_dict["SlowBGToAir"] = process_flux["DecaySlowBGToAir"]
        process_dict["SWStemSnagToAir"] = process_flux["DecaySWStemSnagToAir"]
        process_dict["SWBranchSnagToAir"] = process_flux["DecaySWBranchSnagToAir"]
        process_dict["HWStemSnagToAir"] = process_flux["DecayHWStemSnagToAir"]
        process_dict["HWBranchSnagToAir"] = process_flux["DecayHWBranchSnagToAir"]
        process_dict["GrossGrowth_AG"] = gross_growthAG
        process_dict["GrossGrowth_BG"] = gross_growthBG

        return pd.DataFrame(process_dict)
    
    def concatenated_fluxes_data(self, flux, state, parameters, area):
        """
        Combines disturbance fluxes and annual process fluxes into a single DataFrame.

        Args:
            object: An object holding flux data, area, and state information.

        Returns:
             pandas.DataFrame: DataFrame with concatenated disturbance and process fluxes.
        """
        process_flux = self.create_process_fluxes(flux, state, parameters)
        disturbance_flux = self.create_disturbance_fluxes(flux, state, parameters, area)

        return pd.concat([process_flux, disturbance_flux], axis=0)


    def flux_filter_and_aggregate(self, df):
        filtered_df = df[(df['LandClassID'] == 7) | (df['LandClassID'] == 0)]

        filtered_df_copy = filtered_df.copy()

        filtered_df_copy['DeltaBio'] = (
            (filtered_df['GrossGrowth_AG'] + filtered_df['GrossGrowth_BG']) -
            filtered_df['BiomassToSoil'] - filtered_df['SoftProduction'] - filtered_df['HardProduction'] - filtered_df['DOMProduction'] -
            filtered_df['BioCO2Emission'] - filtered_df['BioCOEmission'] - filtered_df['BioCH4Emission']
        )
        
        filtered_df_copy['DeltaDOM'] = (
            filtered_df['BiomassToSoil'] - filtered_df['DOMCO2Emission'] - filtered_df['DOMCOEmission'] - filtered_df['DOMCH4Emssion'] -
            filtered_df['DOMProduction']
        )
        
        filtered_df_copy['Delta_Ecos'] = filtered_df_copy['DeltaBio'] + filtered_df_copy['DeltaDOM']
        filtered_df_copy['Harvest'] = filtered_df_copy['SoftProduction'] + filtered_df_copy['HardProduction'] + filtered_df_copy['DOMProduction']
        

        
        # Group by 'TimeStep' and calculate sums
        result = filtered_df_copy.groupby(["TimeStep"]).sum()

        return result

