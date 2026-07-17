"""
Flux Manager
============
This module provides tools for scaling, filtering, and transforming carbon flux data 
within the context of a Carbon Budget Model (CBM). It integrates with the CBMpools class
to generate disturbance fluxes and process fluxes while ensuring consistency across data.
"""

from goblin_cbm_runner.resource_manager.managers.cbm_pools import Pools
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
            flux (pandas.DataFrame): DataFrame containing carbon flux data.
            state (pandas.DataFrame): DataFrame containing state information.
            parameters (pandas.DataFrame): DataFrame containing parameter information.
            area (pandas.DataFrame): DataFrame containing area information.

        Returns:
            pandas.DataFrame: DataFrame with augmented flux data ready for CBM use.
        """
        flux = self._add_identifier(flux, state, parameters)

        output = self.filter_flux_data(flux)
       
        return output


    def _add_identifier(self, flux, state, parameters):
        """
        Adds land class and disturbance type columns to an existing flux DataFrame.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.
            state (pandas.DataFrame): DataFrame containing state information.
            parameters (pandas.DataFrame): DataFrame containing parameter information.

        Returns:
            pandas.DataFrame: Flux DataFrame with 'land_class' and 'disturbance_type' columns added.   
        """        

        flux['land_class'] = state['land_class'].values
        flux['disturbance_type'] = parameters['disturbance_type'].values

        return flux


    def create_disturbance_fluxes(self,flux, state, parameters, area):
        """
        Creates a DataFrame of carbon fluxes related to disturbances.

        .. warning::
            This method has not been validated against known reference outputs.
            Ecosystem flux integrity checks (Delta_Ecos ratio via flux_filter_and_aggregate)
            show values in the range 0.7–1.36 instead of the expected 1.0. Use
            AFRunner.run_cbm_flux_scenarios() for validated flux calculations.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.
            state (pandas.DataFrame): DataFrame containing state information.
            parameters (pandas.DataFrame): DataFrame containing parameter information.
            area (pandas.DataFrame): DataFrame containing area information.

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
            flux (pandas.DataFrame): DataFrame containing carbon flux data.

        Returns:
             pandas.Series: A Series representing the total litter production.
        """
        total_litter = flux[self.CBMpools.get_total_litter()].sum(axis=1)

        return total_litter
    
    def create_gross_growthAG(self, flux):
        """
        Calculates the gross growth for aboveground biomass.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.

        Returns:
            pandas.Series: A Series representing the calculated aboveground gross growth.
        """
        
        gross_growth = flux["DeltaBiomass_AG"]+ flux[self.CBMpools.get_gross_growth_AG()].sum(axis=1)

        return gross_growth
    
    def create_gross_growthBG(self, flux):
        """
        Calculates the gross growth for belowground biomass.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.

        Returns:
            pandas.Series: A Series representing the calculated belowground gross growth.
        """            
        gross_growth = flux["DeltaBiomass_BG"]+flux[self.CBMpools.get_gross_growth_BG()].sum(axis=1)

        return gross_growth
    
    def create_process_fluxes(self, flux, state, parameters):
        """
        Creates a DataFrame of annual process fluxes in the CBM.

        .. warning::
            This method has not been validated against known reference outputs.
            Ecosystem flux integrity checks (Delta_Ecos ratio via flux_filter_and_aggregate)
            show values in the range 0.7–1.36 instead of the expected 1.0. Use
            AFRunner.run_cbm_flux_scenarios() for validated flux calculations.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.
            state (pandas.DataFrame): DataFrame containing state information.
            parameters (pandas.DataFrame): DataFrame containing parameter information.

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

        .. warning::
            This method has not been validated against known reference outputs.
            The resulting Delta_Ecos ratio (computed by flux_filter_and_aggregate) falls
            in the range 0.7–1.36 instead of the expected 1.0. Use
            AFRunner.run_cbm_flux_scenarios() for validated flux calculations.

        Args:
            flux (pandas.DataFrame): DataFrame containing carbon flux data.
            state (pandas.DataFrame): DataFrame containing state information.
            parameters (pandas.DataFrame): DataFrame containing parameter information.
            area (pandas.DataFrame): DataFrame containing area information.

        Returns:
             pandas.DataFrame: DataFrame with concatenated disturbance and process fluxes.
        """
        process_flux = self.create_process_fluxes(flux, state, parameters)
        disturbance_flux = self.create_disturbance_fluxes(flux, state, parameters, area)

        return pd.concat([process_flux, disturbance_flux], axis=0)


    def flux_filter_and_aggregate(self, df):
        """
        Filters and aggregates flux data based on specific conditions.

        .. warning::
            This method has not been validated against known reference outputs.
            The resulting Delta_Ecos ratio falls in the range 0.7–1.36 instead of
            the expected 1.0. Use AFRunner.run_cbm_flux_scenarios() for validated
            flux calculations.

        Args:
            df (pandas.DataFrame): DataFrame containing flux data.

        Returns:
            pandas.DataFrame: Aggregated DataFrame with filtered flux data.
        """
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

    @staticmethod
    def aggregate_cbm_flux(df, group_cols):
        """
        Aggregate raw CBM flux table into renamed summary columns.

        Groups a classifier-joined flux DataFrame (from cbm_output.flux) by
        ``group_cols`` and sums the CBM flux columns into descriptive names.
        Intermediate columns (AG litter components, snag components, harvest
        components, disturbance emission components) are preserved for use by
        ``derive_flux_metrics`` and dropped there.

        Litter inputs are split into process (``Turnover*``) and disturbance
        (``Dist_*``) components.  ``derive_flux_metrics`` combines them as
        ``Turnover* + Disturbance*`` to match Kevin Black's CBM-CFS3
        ``MerchLitterInput / OthLitterInput / CoarseLitterInput / ...`` columns,
        which aggregate both sources.  The disturbance terms are substantial
        from the first clearcut rotation onward and must not be omitted.

        Args:
            df (pandas.DataFrame): Classifier-joined flux table with CBM column names.
            group_cols (list[str]): Columns to group by (e.g. ["timestep"] or
                ["timestep", "Species"]).

        Returns:
            pandas.DataFrame: Aggregated flux with renamed columns plus an
            ``identifier``-based ``stand_count`` column.
        """
        return df.groupby(group_cols).agg(
            AGB=("DeltaBiomass_AG", "sum"),
            BGB=("DeltaBiomass_BG", "sum"),
            Fine_root_litter=("TurnoverFineLitterInput", "sum"),
            Coarse_root_litter=("TurnoverCoarseLitterInput", "sum"),
            AG_merch_litter=("TurnoverMerchLitterInput", "sum"),
            AG_fol_litter=("TurnoverFolLitterInput", "sum"),
            AG_oth_litter=("TurnoverOthLitterInput", "sum"),
            Dist_merch_litter=("DisturbanceMerchLitterInput", "sum"),
            Dist_fol_litter=("DisturbanceFolLitterInput", "sum"),
            Dist_oth_litter=("DisturbanceOthLitterInput", "sum"),
            Dist_coarse_litter=("DisturbanceCoarseLitterInput", "sum"),
            Dist_fine_litter=("DisturbanceFineLitterInput", "sum"),
            BGSlow_decay=("DecaySlowBGToAir", "sum"),
            BGVF_decay=("DecayVFastBGToAir", "sum"),
            BGFast_decay=("DecayFastBGToAir", "sum"),
            AGSlow_decay=("DecaySlowAGToAir", "sum"),
            AGVFast_decay=("DecayVFastAGToAir", "sum"),
            AGFast_decay=("DecayFastAGToAir", "sum"),
            Medium_decay=("DecayMediumToAir", "sum"),
            SWStemSnag_decay=("DecaySWStemSnagToAir", "sum"),
            SWBranchSnag_decay=("DecaySWBranchSnagToAir", "sum"),
            HWStemSnag_decay=("DecayHWStemSnagToAir", "sum"),
            HWBranchSnag_decay=("DecayHWBranchSnagToAir", "sum"),
            SoftProduction=("DisturbanceSoftProduction", "sum"),
            HardProduction=("DisturbanceHardProduction", "sum"),
            DOMProduction=("DisturbanceDOMProduction", "sum"),
            BioCO2=("DisturbanceBioCO2Emission", "sum"),
            BioCH4=("DisturbanceBioCH4Emission", "sum"),
            BioCO=("DisturbanceBioCOEmission", "sum"),
            DOMCO2=("DisturbanceDOMCO2Emission", "sum"),
            DOMCH4=("DisturbanceDOMCH4Emission", "sum"),
            DOMCO=("DisturbanceDOMCOEmission", "sum"),
            stand_count=("identifier", "nunique"),
        ).reset_index()

    @staticmethod
    def aggregate_cbm_pools(df, group_cols):
        """
        Aggregate raw CBM pool table into root and soil stock columns.

        Groups a classifier-joined pool DataFrame (from cbm_output.pools) by
        ``group_cols`` and sums the relevant pool columns.

        Args:
            df (pandas.DataFrame): Classifier-joined pool table with CBM column names.
            group_cols (list[str]): Columns to group by (e.g. ["timestep"] or
                ["timestep", "Species"]).

        Returns:
            pandas.DataFrame: Aggregated pool stocks: FineRoot_stock_sw/hw,
            CoarseRoot_stock_sw/hw, BGVF_stock, BGSlow_stock.
        """
        return df.groupby(group_cols).agg(
            FineRoot_stock_sw=("SoftwoodFineRoots", "sum"),
            FineRoot_stock_hw=("HardwoodFineRoots", "sum"),
            CoarseRoot_stock_sw=("SoftwoodCoarseRoots", "sum"),
            CoarseRoot_stock_hw=("HardwoodCoarseRoots", "sum"),
            BGVF_stock=("BelowGroundVeryFastSoil", "sum"),
            BGSlow_stock=("BelowGroundSlowSoil", "sum"),
        ).reset_index()

    @staticmethod
    def derive_flux_metrics(agg, pool_agg, join_cols):
        """
        Derive summary flux metrics from aggregated flux and pool columns.

        Computes combined columns (AG_turnover, Snag_decay, Harvest, BioAtm,
        DOMAtm, Deadwood, Litter, Total_Eco), soil pool estimates (Soil_BGVF,
        Soil_BGSlow, Soil), and merged root stock columns, then drops the
        intermediate columns used to build them.

        Deadwood and Litter use Kevin Black's CBM-CFS3 flux-indicator formulas
        (Kurz et al. 2009, Table 2).  Litter inputs are combined as
        Turnover* + Disturbance* to match Kevin's ``MerchLitterInput`` etc.
        which aggregate both sources.  Pool groupings follow Table 2:
          Deadwood = StemSnags + BranchSnags + MediumSoil + BelowGroundFastSoil
          Litter   = AboveGroundVeryFast + AboveGroundFast + AboveGroundSlow
          Soil     = BelowGroundVeryFast + BelowGroundSlow

        Deadwood formula (KB / Kurz 2009 Table 2):
            DW_Inflow  = MerchLitter + OthLitter × 0.25 + CoarseLitter × 0.5
            DW_Outflow = Snag_decay + DOMProduction + Medium_decay + BGFast_decay
            Deadwood   = DW_Inflow − DW_Outflow

        Litter formula (KB / Kurz 2009 Table 2):
            LT_Inflow  = FolLitter + OthLitter × 0.75 + CoarseLitter × 0.5
                         + FineLitter × 0.5
            LT_Outflow = AGVFast_decay + AGFast_decay + AGSlow_decay
            Litter     = LT_Inflow − LT_Outflow

        Soil_BGVF uses the corrected formula:
            Fine_root_litter × 0.5 − BGVF_decay
        where 0.5 is (1 − fine_ag_split) from the AIDB. TurnoverFineLitterInput
        is the pre-split total; only 50% enters BGVF.

        Soil_BGSlow is set to ``−BGSlow_decay`` as a placeholder. This omits the
        slow-mixing transfer (AboveGroundSlowSoil → BGSlow at 0.006/yr) which
        has no named flux column in libcbm. Callers that need an accurate
        Soil_BGSlow must override it with the BGSlow pool-delta after calling
        this method. See ``AF_raw_cbm_flux`` for the canonical implementation.

        Args:
            agg (pandas.DataFrame): Output of ``aggregate_cbm_flux``.
            pool_agg (pandas.DataFrame): Output of ``aggregate_cbm_pools`` for
                the same timestep range (timestep >= 1).
            join_cols (list[str]): Columns used to merge ``agg`` and ``pool_agg``
                (must match ``group_cols`` used in both aggregation calls).

        Returns:
            pandas.DataFrame: ``agg`` with derived columns added and intermediate
            columns removed.
        """
        agg["AG_turnover"] = agg["AG_merch_litter"] + agg["AG_fol_litter"] + agg["AG_oth_litter"]
        agg["Snag_decay"]  = (agg["SWStemSnag_decay"] + agg["SWBranchSnag_decay"]
                              + agg["HWStemSnag_decay"] + agg["HWBranchSnag_decay"])
        agg["Harvest"]     = agg["SoftProduction"] + agg["HardProduction"] + agg["DOMProduction"]
        agg["BioAtm"]      = agg["BioCO2"] + agg["BioCH4"] + agg["BioCO"]
        agg["DOMAtm"]      = agg["DOMCO2"] + agg["DOMCH4"] + agg["DOMCO"]

        # Combined litter (process + disturbance) — matches Kevin's MerchLitterInput etc.
        merch_litter  = agg["AG_merch_litter"]    + agg["Dist_merch_litter"]
        fol_litter    = agg["AG_fol_litter"]      + agg["Dist_fol_litter"]
        oth_litter    = agg["AG_oth_litter"]      + agg["Dist_oth_litter"]
        coarse_litter = agg["Coarse_root_litter"] + agg["Dist_coarse_litter"]
        fine_litter   = agg["Fine_root_litter"]   + agg["Dist_fine_litter"]

        # Kevin's Deadwood formula (Kurz et al. 2009 Table 2)
        agg["Deadwood"] = (
            merch_litter + oth_litter * 0.25 + coarse_litter * 0.5
            - agg["Snag_decay"] - agg["DOMProduction"]
            - agg["Medium_decay"] - agg["BGFast_decay"]
        )

        # Kevin's Litter formula (Kurz et al. 2009 Table 2)
        agg["Litter"] = (
            fol_litter + oth_litter * 0.75 + coarse_litter * 0.5 + fine_litter * 0.5
            - agg["AGVFast_decay"] - agg["AGFast_decay"] - agg["AGSlow_decay"]
        )

        agg["Soil_BGVF"]   = agg["Fine_root_litter"] * 0.5 - agg["BGVF_decay"]
        # placeholder — caller should override with BGSlow pool-delta for accuracy
        agg["Soil_BGSlow"] = -agg["BGSlow_decay"]
        agg["Soil"]        = agg["Soil_BGVF"] + agg["Soil_BGSlow"]

        all_litter = agg["Fine_root_litter"] + agg["Coarse_root_litter"] + agg["AG_turnover"]
        all_decay  = (agg["BGVF_decay"] + agg["BGFast_decay"] + agg["BGSlow_decay"]
                      + agg["AGVFast_decay"] + agg["AGFast_decay"] + agg["AGSlow_decay"]
                      + agg["Medium_decay"] + agg["Snag_decay"])
        agg["Total_Eco"] = (agg["AGB"] + agg["BGB"]
                            + all_litter - all_decay
                            - agg["Harvest"] - agg["BioAtm"] - agg["DOMAtm"])

        agg = agg.merge(pool_agg, on=join_cols)
        agg["FineRoot_stock"]   = agg["FineRoot_stock_sw"] + agg["FineRoot_stock_hw"]
        agg["CoarseRoot_stock"] = agg["CoarseRoot_stock_sw"] + agg["CoarseRoot_stock_hw"]

        return agg.drop(columns=[
            "AG_merch_litter", "AG_fol_litter", "AG_oth_litter",
            "Dist_merch_litter", "Dist_fol_litter", "Dist_oth_litter",
            "Dist_coarse_litter", "Dist_fine_litter",
            "SWStemSnag_decay", "SWBranchSnag_decay", "HWStemSnag_decay", "HWBranchSnag_decay",
            "SoftProduction", "HardProduction", "DOMProduction",
            "BioCO2", "BioCH4", "BioCO", "DOMCO2", "DOMCH4", "DOMCO",
            "FineRoot_stock_sw", "FineRoot_stock_hw",
            "CoarseRoot_stock_sw", "CoarseRoot_stock_hw",
        ])

