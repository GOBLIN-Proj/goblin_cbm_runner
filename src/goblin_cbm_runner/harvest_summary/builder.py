"""
Harvest Summary Builder
========================
Builds per-species-per-timestep harvest and NAI summaries from CBMOutput data.

Produces two compact DataFrames that match Kevin Black's CBM-CFS3 query outputs:
  - Disturbance Summary: per timestep × species × disturbance type
  - NAI Summary: per timestep × species (merchantable stock, harvest, NAI)

These are generated from the per-stand data that CBMOutput accumulates during
simulation (pools, flux, parameters, classifiers, area), aggregated by species.
"""
import pandas as pd
import numpy as np


class HarvestSummaryBuilder:
    """Builds per-species-per-timestep harvest and NAI summaries from cbm_output."""

    # Species prefix → basic wood density (t/m3).
    # Volume = Carbon / (carbon_fraction × density) = Carbon × (2 / density).
    # Matched by longest prefix against classifier species names.
    BASIC_DENSITY = {
        'Spruce': 0.40,
        'Pine': 0.44,
        'Cmix': 0.42,
        'OC': 0.45,
        'Cbmix-Conifer': 0.51,
        'Cbmix-Bl': 0.51,
        'SNFGB': 0.56,
        'FGB': 0.56,
        'SGB': 0.70,
    }

    # Carbon fraction of dry biomass (standard CBM assumption)
    CARBON_FRACTION = 0.5

    @staticmethod
    def build(cbm_output, year_range, disturbance_id_map=None,
              disturbance_name_map=None):
        """
        Build disturbance and NAI summary tables from CBMOutput.

        Args:
            cbm_output: CBMOutput with accumulated simulation data (pools, flux,
                parameters, classifiers, area).
            year_range: list mapping timestep index to calendar year.
                year_range[0] = year for timestep 0, etc.
            disturbance_id_map: dict mapping integer disturbance IDs to SIT ID
                strings (e.g., {1: "DISTID1"}). From sit.disturbance_id_map.
            disturbance_name_map: dict mapping integer disturbance IDs to
                human-readable names (e.g., {1: "Clearcut"}). From
                sit.disturbance_name_map.

        Returns:
            dict with keys:
                'disturbance_summary': DataFrame — per timestep × species × dist type
                'nai_summary': DataFrame — per timestep × species
        """
        # Convert CBMOutput tables to pandas
        classifiers_df = cbm_output.classifiers.to_pandas()
        pools_df = cbm_output.pools.to_pandas()
        flux_df = cbm_output.flux.to_pandas()
        params_df = cbm_output.parameters.to_pandas()
        area_df = cbm_output.area.to_pandas()
        state_df = cbm_output.state.to_pandas() if cbm_output.state is not None else None

        # Build timestep → year mapping
        ts_to_year = {i: y for i, y in enumerate(year_range)}

        # Determine species column name (first classifier column that isn't
        # 'identifier' or 'timestep')
        species_col = HarvestSummaryBuilder._find_species_column(classifiers_df)

        # Map disturbance types
        params_df = HarvestSummaryBuilder._map_disturbance_types(
            params_df, disturbance_id_map, disturbance_name_map
        )

        # --- Disturbance Summary ---
        dist_summary = HarvestSummaryBuilder._build_disturbance_summary(
            classifiers_df, flux_df, params_df, area_df, species_col, ts_to_year,
            state_df=state_df
        )

        # --- NAI Summary ---
        nai_summary = HarvestSummaryBuilder._build_nai_summary(
            classifiers_df, pools_df, flux_df, params_df, area_df,
            species_col, ts_to_year, dist_summary, state_df=state_df
        )

        return {
            'disturbance_summary': dist_summary,
            'nai_summary': nai_summary,
        }

    @staticmethod
    def add_expected(summary_dict, disturbance_events_df, runner_type='FM'):
        """
        Add Expected and Diff columns to the disturbance summary by matching
        with the input disturbance_events.csv.

        Args:
            summary_dict: dict from build() with 'disturbance_summary' key.
            disturbance_events_df: DataFrame from disturbance_events.csv.
            runner_type: 'FM', 'AF', or 'SC' — determines column name mapping.

        Returns:
            Updated summary_dict (modified in place and returned).
        """
        dist_summary = summary_dict['disturbance_summary']

        expected = HarvestSummaryBuilder._parse_disturbance_events(
            disturbance_events_df, runner_type
        )

        if expected is not None and not expected.empty:
            dist_summary = dist_summary.merge(
                expected,
                on=['TimeStep', 'SP', 'DistTypeName'],
                how='left'
            )
            dist_summary['Diff'] = np.where(
                dist_summary['Expected'].notna() & (dist_summary['Expected'] != 0),
                (dist_summary['Provided'] - dist_summary['Expected']) / dist_summary['Expected'],
                np.nan
            )
        else:
            dist_summary['Expected'] = np.nan
            dist_summary['Diff'] = np.nan

        summary_dict['disturbance_summary'] = dist_summary
        return summary_dict

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_species_column(classifiers_df):
        """Find the species classifier column name."""
        # libcbm names columns by classifier value (e.g., 'Species')
        # or by number (e.g., 'Classifier1'). Check for common names.
        for col in classifiers_df.columns:
            if col.lower() == 'species':
                return col
        # Fallback: first column that isn't identifier/timestep
        for col in classifiers_df.columns:
            if col not in ('identifier', 'timestep'):
                return col
        raise ValueError("No species classifier column found in classifiers")

    @staticmethod
    def _map_disturbance_types(params_df, disturbance_id_map, disturbance_name_map):
        """Map disturbance_type column to DISTID codes and human names."""
        dt = params_df['disturbance_type']

        if pd.api.types.is_numeric_dtype(dt):
            # Raw integer IDs → map to DISTID and human name
            if disturbance_id_map:
                params_df['DistTypeName'] = dt.map(disturbance_id_map).fillna('Unknown')
            else:
                params_df['DistTypeName'] = dt.astype(str)

            if disturbance_name_map:
                params_df['DistTypeDesc'] = dt.map(disturbance_name_map).fillna('Unknown')
            else:
                params_df['DistTypeDesc'] = params_df['DistTypeName']
        else:
            # Already mapped to human-readable names (comprehensive mode)
            params_df['DistTypeDesc'] = dt
            # Reverse-map to get DISTID codes
            if disturbance_name_map and disturbance_id_map:
                reverse_name = {v: k for k, v in disturbance_name_map.items()}
                int_ids = dt.map(reverse_name)
                params_df['DistTypeName'] = int_ids.map(disturbance_id_map).fillna(dt)
            else:
                params_df['DistTypeName'] = dt

        return params_df

    @staticmethod
    def _build_disturbance_summary(classifiers_df, flux_df, params_df, area_df,
                                   species_col, ts_to_year, state_df=None):
        """Build per-timestep × species × disturbance-type summary."""
        # Merge: classifiers + flux + parameters + area on (identifier, timestep)
        merge_keys = ['identifier', 'timestep']

        # Select flux columns — include DOMProduction if present (KB: add harvest
        # from standing dead trees to merchantable C values before volume conversion)
        flux_cols = ['DisturbanceSoftProduction', 'DisturbanceHardProduction']
        if 'DisturbanceDOMProduction' in flux_df.columns:
            flux_cols.append('DisturbanceDOMProduction')

        merged = classifiers_df[merge_keys + [species_col]].merge(
            flux_df[merge_keys + flux_cols],
            on=merge_keys
        ).merge(
            params_df[merge_keys + ['DistTypeName', 'DistTypeDesc']],
            on=merge_keys
        ).merge(
            area_df.rename(columns={area_df.columns[-1]: 'area'})[merge_keys + ['area']],
            on=merge_keys
        )

        # Filter to forest land only (KB: land_class == 0 = Forest land).
        # Exception: DISTID7 (deforestation) is always included regardless of
        # post-disturbance land_class — the harvest occurred on forest land before
        # the land conversion was recorded in the state table.
        if state_df is not None and 'land_class' in state_df.columns:
            forest_ids = state_df.loc[state_df['land_class'] == 0, merge_keys]
            forest_merged = merged.merge(forest_ids, on=merge_keys)
            deforest_merged = merged[merged['DistTypeName'] == 'DISTID7']
            merged = pd.concat([forest_merged, deforest_merged]).drop_duplicates()

        # Group by (timestep, species, disturbance type)
        agg_dict = {
            'SoftwoodHarvest_tC': ('DisturbanceSoftProduction', 'sum'),
            'HardwoodHarvest_tC': ('DisturbanceHardProduction', 'sum'),
        }
        if 'DisturbanceDOMProduction' in merged.columns:
            agg_dict['DOMHarvest_tC'] = ('DisturbanceDOMProduction', 'sum')

        grouped = merged.groupby(
            ['timestep', species_col, 'DistTypeName', 'DistTypeDesc']
        ).agg(**agg_dict).reset_index()

        # Compute derived columns — Provided includes DOM harvest (KB requirement)
        grouped['Provided'] = grouped['SoftwoodHarvest_tC'] + grouped['HardwoodHarvest_tC']
        if 'DOMHarvest_tC' in grouped.columns:
            grouped['Provided'] = grouped['Provided'] + grouped['DOMHarvest_tC']
        grouped['Measurement_type'] = 'M'

        # Volume conversion
        grouped['Vol'] = grouped.apply(
            lambda row: row['Provided'] * HarvestSummaryBuilder._carbon_to_volume_factor(
                row[species_col]
            ),
            axis=1
        )

        # Map timestep → year
        grouped['Year'] = grouped['timestep'].map(ts_to_year)

        # Filter: only rows where something actually happened (Provided > 0)
        grouped = grouped[grouped['Provided'] > 0].copy()

        # Rename and reorder
        grouped = grouped.rename(columns={
            'timestep': 'TimeStep',
            species_col: 'SP',
        })

        column_order = [
            'TimeStep', 'Year', 'SP', 'Measurement_type', 'DistTypeName',
            'DistTypeDesc', 'Provided', 'SoftwoodHarvest_tC', 'HardwoodHarvest_tC',
            'DOMHarvest_tC', 'Vol',
        ]
        return grouped[[c for c in column_order if c in grouped.columns]].sort_values(
            ['TimeStep', 'SP', 'DistTypeName']
        ).reset_index(drop=True)

    @staticmethod
    def _build_nai_summary(classifiers_df, pools_df, flux_df, params_df, area_df,
                           species_col, ts_to_year, dist_summary, state_df=None):
        """Build per-timestep × species NAI summary."""
        merge_keys = ['identifier', 'timestep']

        # Merge classifiers + pools + area
        merged = classifiers_df[merge_keys + [species_col]].merge(
            pools_df[merge_keys + ['SoftwoodMerch', 'HardwoodMerch']],
            on=merge_keys
        ).merge(
            area_df.rename(columns={area_df.columns[-1]: 'area'})[merge_keys + ['area']],
            on=merge_keys
        )

        # Filter to forest land only (KB: land_class == 0 = Forest land)
        if state_df is not None and 'land_class' in state_df.columns:
            forest_ids = state_df.loc[state_df['land_class'] == 0, merge_keys]
            merged = merged.merge(forest_ids, on=merge_keys)

        # Group by (timestep, species): sum merch pools and area
        stock = merged.groupby(['timestep', species_col]).agg(
            SoftwoodMerch_tC=('SoftwoodMerch', 'sum'),
            HardwoodMerch_tC=('HardwoodMerch', 'sum'),
            SumOfTA=('area', 'sum'),
        ).reset_index()

        stock['GrossC'] = stock['SoftwoodMerch_tC'] + stock['HardwoodMerch_tC']

        # Get harvest totals per timestep × species from disturbance summary
        if not dist_summary.empty:
            harvest = dist_summary.groupby(['TimeStep', 'SP']).agg(
                HarvestC=('Provided', 'sum'),
                SoftwoodHarvestC=('SoftwoodHarvest_tC', 'sum'),
                HardwoodHarvestC=('HardwoodHarvest_tC', 'sum'),
            ).reset_index()
        else:
            harvest = pd.DataFrame(columns=['TimeStep', 'SP', 'HarvestC',
                                            'SoftwoodHarvestC', 'HardwoodHarvestC'])

        # Merge stock with harvest
        stock = stock.rename(columns={'timestep': 'TimeStep', species_col: 'SP'})
        nai = stock.merge(harvest, on=['TimeStep', 'SP'], how='left')
        nai['HarvestC'] = nai['HarvestC'].fillna(0)
        nai['SoftwoodHarvestC'] = nai['SoftwoodHarvestC'].fillna(0)
        nai['HardwoodHarvestC'] = nai['HardwoodHarvestC'].fillna(0)

        # SumOfMerch = remaining stock (GrossC is stock including what was harvested,
        # but pools are post-harvest state, so GrossC IS the remaining stock)
        # Actually, pools reflect post-disturbance state. GrossC = what's left.
        # SumOfMerch in Kevin's output is the same as GrossC (post-harvest).
        nai['SumOfMerch'] = nai['GrossC']

        # Compute NAI per species: NAI[t] = GrossC[t] - GrossC[t-1] + HarvestC[t]
        # GrossC[t] is post-harvest, so the growth is hidden by the harvest removal.
        # Adding HarvestC back recovers the true growth (NAI).
        nai = nai.sort_values(['SP', 'TimeStep']).reset_index(drop=True)
        nai['GrossC_prev'] = nai.groupby('SP')['GrossC'].shift(1)
        nai['NAI'] = np.where(
            nai['GrossC_prev'].notna(),
            nai['GrossC'] - nai['GrossC_prev'] + nai['HarvestC'],
            np.nan
        )

        # Harvest ratio
        nai['Harvest ratio'] = np.where(
            nai['NAI'].notna() & (nai['NAI'] != 0),
            nai['HarvestC'] / nai['NAI'],
            np.nan
        )

        # Volume conversions
        nai['GrossVol'] = nai.apply(
            lambda row: row['GrossC'] * HarvestSummaryBuilder._carbon_to_volume_factor(
                row['SP']
            ),
            axis=1
        )
        nai['HarvestVol'] = nai.apply(
            lambda row: row['HarvestC'] * HarvestSummaryBuilder._carbon_to_volume_factor(
                row['SP']
            ),
            axis=1
        )

        # Map timestep → year
        nai['Year'] = nai['TimeStep'].map(ts_to_year)

        # Reorder columns
        column_order = [
            'TimeStep', 'Year', 'SP', 'GrossC', 'GrossVol',
            'HarvestC', 'HarvestVol', 'SoftwoodHarvestC', 'HardwoodHarvestC',
            'SoftwoodMerch_tC', 'HardwoodMerch_tC',
            'SumOfMerch', 'SumOfTA', 'NAI', 'Harvest ratio',
        ]

        # Drop helper column
        nai = nai.drop(columns=['GrossC_prev'], errors='ignore')

        return nai[[c for c in column_order if c in nai.columns]].sort_values(
            ['TimeStep', 'SP']
        ).reset_index(drop=True)

    @staticmethod
    def _carbon_to_volume_factor(species_name):
        """Get carbon-to-volume conversion factor for a species.

        Returns 2 / basic_density (m3 per tC). Matches by longest prefix.
        Falls back to softwood default (0.45 t/m3) if no match.
        """
        if not isinstance(species_name, str):
            return 2.0 / 0.45  # default

        # Strip common prefixes used in SC classifiers
        name = species_name
        for prefix in ('NF_', 'IE_'):
            if name.startswith(prefix):
                name = name[len(prefix):]

        # Match by longest prefix
        best_match = None
        best_len = 0
        for prefix, density in HarvestSummaryBuilder.BASIC_DENSITY.items():
            if name.startswith(prefix) and len(prefix) > best_len:
                best_match = density
                best_len = len(prefix)

        if best_match is not None:
            return 2.0 / best_match

        # Fallback
        return 2.0 / 0.45

    @staticmethod
    def _parse_disturbance_events(df, runner_type):
        """Parse disturbance_events.csv into Expected targets by timestep/species/dist_type.

        Handles both FM format (Measurement_type, Dist_Type_ID, Step)
        and SC format (MeasureType, DistTypeID, Year).

        Returns DataFrame with columns: TimeStep, SP, DistTypeName, Expected
        """
        df = df.copy()

        # Normalize column names across FM/AF and SC formats
        col_map = {}
        for col in df.columns:
            cl = col.lower().replace('_', '')
            if cl in ('classifier1',):
                col_map[col] = 'species'
            elif cl in ('measurementtype', 'measuretype', 'meastype'):
                col_map[col] = 'mtype'
            elif cl in ('disttypeid', 'disttypename'):
                col_map[col] = 'dist_type'
            elif cl in ('step', 'year'):
                col_map[col] = 'timestep'
            elif cl == 'amount':
                col_map[col] = 'amount'

        df = df.rename(columns=col_map)

        required = {'species', 'mtype', 'dist_type', 'timestep', 'amount'}
        if not required.issubset(df.columns):
            return None

        # Filter to merchantable targets only (type M)
        merch = df[df['mtype'] == 'M'].copy()
        if merch.empty:
            return None

        # Group by timestep × species × dist_type, sum Amount
        expected = merch.groupby(['timestep', 'species', 'dist_type']).agg(
            Expected=('amount', 'sum')
        ).reset_index()

        expected = expected.rename(columns={
            'timestep': 'TimeStep',
            'species': 'SP',
            'dist_type': 'DistTypeName',
        })

        # Ensure TimeStep is int
        expected['TimeStep'] = expected['TimeStep'].astype(int)

        return expected
