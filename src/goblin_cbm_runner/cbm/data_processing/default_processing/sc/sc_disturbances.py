"""
SC Disturbances Module
======================
Generates disturbance events for scenario forest simulations.

Three types of events:
1. DISTID4 (Afforestation) - when forest is planted
2. DISTID1/2 (Harvest) - clearfell/thinning via AfforestationTracker
3. DISTID3 (Fire) - annual fire proportional to national fire rate
"""
import pandas as pd
from goblin_cbm_runner.resource_manager import Loader
from goblin_cbm_runner.harvest_manager.harvest import AfforestationTracker
from goblin_cbm_runner.cbm.data_processing.default_processing.sc.sc_inventory import SCInventory


class SCDisturbances:
    """
    Generates disturbance_events.csv for scenarios.

    Handles afforestation (DISTID4), harvest (DISTID1/2), and fire (DISTID3).
    Uses AfforestationTracker for harvest simulation with stand splitting.
    Fire rate derived from combined FM + AF national fire data.

    Args:
        data_manager: SCDataManager instance
        scenario: Scenario number (0, 1, 2, ...)
    """

    def __init__(self, data_manager, scenario):
        self.data_manager = data_manager
        self.scenario = scenario
        self.loader = Loader()
        self.inventory_class = SCInventory(data_manager)

        # Get configuration
        self.baseline_year = data_manager.get_forest_baseline_year()
        self.end_year = data_manager.get_forest_end_year()
        self.afforestation_end_year = data_manager.get_afforestation_end_year()
        self.afforest_delay = data_manager.get_afforest_delay()
        self.annual_rate_pre_delay = data_manager.get_annual_rate_pre_delay()

        # Get disturbance columns from config
        self.disturbance_cols = data_manager.get_disturbance_cols()
        self.static_cols = data_manager.get_static_disturbance_cols()

        # Get mappings
        self.transition_dict = data_manager.get_transition_dict_species()

    def fill_scenario_data(self, inventory_df):
        """
        Generate all disturbance events for the scenario.

        Args:
            inventory_df: DataFrame from SCInventory.scenario_inventory()

        Returns:
            DataFrame: Combined DISTID4, DISTID1/2, and DISTID3 events
        """
        # Step 1: Generate DISTID4 (afforestation) events
        afforestation_events = self._generate_afforestation_events(inventory_df)

        # Step 2: Generate DISTID1/2 (harvest) events via tracker
        harvest_events = self._generate_harvest_events(afforestation_events)

        # Step 3: Generate DISTID3 (fire) events from national fire rate
        fire_events = self._generate_fire_events(afforestation_events)

        # Step 4: Combine and format
        if afforestation_events.empty and harvest_events.empty:
            raise ValueError("Both afforestation and harvest disturbances are empty.")

        dfs = [df for df in [afforestation_events, harvest_events, fire_events] if not df.empty]
        combined = pd.concat(dfs, ignore_index=True)

        return combined

    def _generate_afforestation_events(self, inventory_df):
        """
        Generate DISTID4 events for each year.

        Inventory represents the TOTAL area to afforest over the afforestation period.
        - During delay period: uses annual_rate_pre_delay distributed proportionally
        - After delay: remaining area (inventory - pre_delay) is annualized

        Args:
            inventory_df: Inventory with columns Classifier1-4, Area

        Returns:
            DataFrame: DISTID4 events in SIT format
        """
        simulation_years = self.afforestation_end_year - self.baseline_year
        events = []

        # Calculate total area from inventory (this is the TOTAL to afforest)
        total_inventory_area = inventory_df["Area"].sum()
        if total_inventory_area == 0:
            return pd.DataFrame(columns=self.disturbance_cols)

        # Calculate area proportions per inventory row
        inventory_df = inventory_df.copy()
        inventory_df["proportion"] = inventory_df["Area"] / total_inventory_area

        # Calculate pre-delay total (area used during delay period)
        pre_delay_total = self.annual_rate_pre_delay * self.afforest_delay

        # Calculate remaining area for post-delay period
        remaining_area = total_inventory_area - pre_delay_total

        # Validate: pre-delay cannot exceed inventory total
        if remaining_area < 0:
            import warnings
            warnings.warn(
                f"Pre-delay area ({pre_delay_total:,.0f} ha) exceeds inventory total "
                f"({total_inventory_area:,.0f} ha). Capping pre-delay to inventory total."
            )
            # Cap pre-delay to inventory total, no post-delay
            pre_delay_total = total_inventory_area
            remaining_area = 0
            # Adjust effective delay to consume all inventory
            effective_delay = int(total_inventory_area / self.annual_rate_pre_delay) if self.annual_rate_pre_delay > 0 else 0
        else:
            effective_delay = self.afforest_delay

        # Calculate annualized scenario rate (post-delay)
        post_delay_years = simulation_years - self.afforest_delay
        if post_delay_years > 0 and remaining_area > 0:
            annualized_rate = remaining_area / post_delay_years
        else:
            annualized_rate = 0

        for year in range(1, simulation_years + 1):
            # Determine annual rate based on delay period
            if year <= self.afforest_delay:
                # During delay: use pre-delay rate (but cap to remaining inventory)
                if year <= effective_delay:
                    annual_rate = self.annual_rate_pre_delay
                else:
                    annual_rate = 0  # Inventory exhausted during delay
            else:
                annual_rate = annualized_rate

            # Skip if no area to plant
            if annual_rate == 0:
                continue

            # Generate events for each inventory row
            for _, row in inventory_df.iterrows():
                area = annual_rate * row["proportion"]
                if area <= 0:
                    continue

                # Inventory already has NF_* species (non-forest land)
                # Use as-is for DISTID4 events - transition rules handle conversion
                event = self._create_disturbance_row(
                    classifier1=row["Classifier1"],
                    classifier2=row["Classifier2"],
                    classifier3=row["Classifier3"],
                    classifier4=row["Classifier4"],
                    dist_type="DISTID4",
                    year=year,
                    amount=area
                )
                events.append(event)

        return pd.DataFrame(events, columns=self.disturbance_cols) if events else pd.DataFrame(columns=self.disturbance_cols)

    def _generate_harvest_events(self, afforestation_df):
        """
        Generate DISTID1/2 events via AfforestationTracker.

        Args:
            afforestation_df: DataFrame of DISTID4 events

        Returns:
            DataFrame: DISTID1/2 events in SIT format
        """
        if afforestation_df.empty:
            return pd.DataFrame(columns=self.disturbance_cols)

        # Build disturbance_dict from scenario_data
        disturbance_dict = self._build_disturbance_dict()
        if not disturbance_dict:
            return pd.DataFrame(columns=self.disturbance_cols)

        # Prepare forest_df for tracker
        # Tracker expects: Classifier1-4, Amount, Year
        forest_df = self._prepare_forest_df(afforestation_df)

        if forest_df.empty:
            return pd.DataFrame(columns=self.disturbance_cols)

        # Run tracker
        simulation_years = self.end_year - self.baseline_year
        tracker = AfforestationTracker(
            data_manager=self.data_manager,
            disturdance_dict=disturbance_dict,
            forest_df=forest_df,
            years=simulation_years
        )

        raw_events = tracker.run_simulation()

        # Format output
        return self._format_harvest_events(raw_events)

    def _build_disturbance_dict(self):
        """
        Build disturbance proportions dict from scenario_data.

        Returns:
            dict: {species: {DISTID1: proportion, DISTID2: proportion}}
        """
        scenario_data = self.data_manager.get_scenario_data()

        # Find the row for this scenario
        scenario_row = scenario_data[scenario_data["Scenarios"] == self.scenario]
        if scenario_row.empty:
            # Try without 's'
            scenario_row = scenario_data[scenario_data.get("Scenario", pd.Series()) == self.scenario]
        if scenario_row.empty:
            return {}

        # Extract harvest proportions
        # Expected columns: "Conifer harvest", "Conifer thinned", "Broadleaf harvest", "Broadleaf thinned"
        conifer_harvest = scenario_row.get("Conifer harvest", pd.Series([0])).iloc[0]
        conifer_thinned = scenario_row.get("Conifer thinned", pd.Series([0])).iloc[0]
        broadleaf_harvest = scenario_row.get("Broadleaf harvest", pd.Series([0])).iloc[0]
        broadleaf_thinned = scenario_row.get("Broadleaf thinned", pd.Series([0])).iloc[0]

        # Build dict for each species
    
        #To CLAUDE: I have updated this, we should only be looking at the species in the inventory. If we go beyond that we apply afforestation events to species and yield that are not there. 
        species_list = [s.replace("NF_", "") for s in self.inventory_class.scenario_inventory(self.scenario)["Classifier1"].unique()]
        
        #species_list =list(self.data_manager.get_transition_dict_species_to_yield().keys()) Cluade's previous implmentation, does not reflect inventory.

        disturbance_dict = {}
        for species in species_list:
            # Simple classification: SGB is broadleaf, rest are conifers
            if "SGB" in species or "FGB" in species or "OC" in species:
                disturbance_dict[species] = {
                    "DISTID1": broadleaf_harvest,
                    "DISTID2": broadleaf_thinned
                }
            else:
                disturbance_dict[species] = {
                    "DISTID1": conifer_harvest,
                    "DISTID2": conifer_thinned
                }

        return disturbance_dict

    def _prepare_forest_df(self, afforestation_df):
        """
        Prepare forest_df for AfforestationTracker.

        Converts afforestation events to standing forest format.
        Tracker expects Classifier2="A" for afforestation input.
        """
        if afforestation_df.empty:
            return pd.DataFrame()

        # Select relevant columns
        cols = ["Classifier1", "Classifier2", "Classifier3", "Classifier4", "Amount", "Year"]
        forest_df = afforestation_df[cols].copy()

        return forest_df

    def _format_harvest_events(self, raw_events):
        """
        Format raw tracker output to SIT disturbance format.

        Args:
            raw_events: DataFrame from tracker.run_simulation()

        Returns:
            DataFrame: Formatted with all disturbance columns
        """
        if raw_events.empty:
            return pd.DataFrame(columns=self.disturbance_cols)

        events = []
        for _, row in raw_events.iterrows():
            event = self._create_disturbance_row(
                classifier1=row["Classifier1"],
                classifier2=row["Classifier2"],
                classifier3=row["Classifier3"],
                classifier4=row["Classifier4"],
                dist_type=row["DistTypeID"],
                year=row["Year"],
                amount=row["Amount"]
            )

            # Update age constraints from Disturbance_timing
            self._update_timing(event, row["Classifier1"], row["Classifier4"], row["DistTypeID"])
            events.append(event)

        return pd.DataFrame(events, columns=self.disturbance_cols)

    def _create_disturbance_row(self, classifier1, classifier2, classifier3, classifier4,
                                 dist_type, year, amount):
        """
        Create a single disturbance event row with all required columns.
        """
        # Static defaults (all -1)
        static_defaults = {col: -1 for col in self.static_cols}

        row = {
            "Classifier1": classifier1,
            "Classifier2": classifier2,
            "Classifier3": classifier3,
            "Classifier4": classifier4,
            "UsingID": False,
            "sw_age_min": 0,
            "sw_age_max": 210,
            "hw_age_min": 0,
            "hw_age_max": 210,
            "MinYearsSinceDist": -1,
            **static_defaults,
            "Efficiency": 1,
            "SortType": 3,  # SORT_BY_SW_AGE
            "MeasureType": "A",  # Area-based
            "Amount": amount,
            "DistTypeID": dist_type,
            "Year": year,
        }
        return row

    def _update_timing(self, row, species, yield_class, dist_type):
        """
        Update row with Disturbance_timing constraints.
        """
        disturbance_timing = self.loader.disturbance_time()
        yield_name_dict = self.data_manager.get_yield_name_dict()

        try:
            cohort = yield_name_dict.get(species, {}).get(yield_class, species)
            timing_row = disturbance_timing.loc[
                (disturbance_timing.index == cohort) &
                (disturbance_timing["disturbance_id"] == dist_type)
            ]

            if not timing_row.empty:
                row["sw_age_min"] = int(timing_row["sw_age_min"].iloc[0])
                row["sw_age_max"] = int(timing_row["sw_age_max"].iloc[0])
                row["hw_age_min"] = int(timing_row["hw_age_min"].iloc[0])
                row["hw_age_max"] = int(timing_row["hw_age_max"].iloc[0])
                row["MinYearsSinceDist"] = int(timing_row["min_years_since_dist"].iloc[0])
        except (KeyError, ValueError):
            # Keep defaults if lookup fails
            pass

    # =========================================================================
    # DISTID3 (Fire) — derived from national FM + AF fire rate
    # =========================================================================

    def _generate_fire_events(self, afforestation_df):
        """
        Generate DISTID3 fire events scaled by national fire rate.

        Calculates a per-hectare annual fire rate from combined FM + AF
        disturbance data, then applies it to the cumulative SC afforested
        area at each simulation year.

        Fire events use wildcard classifiers (species-agnostic) and
        SortType=6 (random), matching FM/AF fire event format.

        Args:
            afforestation_df: DataFrame of DISTID4 events (with Amount and Year)

        Returns:
            DataFrame: DISTID3 events in SIT format
        """
        if afforestation_df.empty:
            return pd.DataFrame(columns=self.disturbance_cols)

        fire_rate = self._calculate_national_fire_rate()
        if fire_rate <= 0:
            return pd.DataFrame(columns=self.disturbance_cols)

        # Build cumulative afforested area by simulation year
        area_by_year = afforestation_df.groupby("Year")["Amount"].sum().sort_index()
        cumulative_area = area_by_year.cumsum()

        simulation_years = self.end_year - self.baseline_year
        events = []

        for year in range(1, simulation_years + 1):
            # Forward-fill: use latest cumulative area at or before this year
            valid = cumulative_area[cumulative_area.index <= year]
            if valid.empty:
                continue

            area_at_year = valid.iloc[-1]
            fire_area = fire_rate * area_at_year

            if fire_area <= 0:
                continue

            event = self._create_fire_row(year, fire_area)
            events.append(event)

        if not events:
            return pd.DataFrame(columns=self.disturbance_cols)

        return pd.DataFrame(events, columns=self.disturbance_cols)

    def _calculate_national_fire_rate(self):
        """
        Calculate national fire rate (ha burned per ha forest per year).

        Combines FM and AF fire events (DISTID3) and divides by
        combined FM + AF inventory area to get a per-hectare rate.

        Returns:
            float: Annual fire rate (ha/ha/year). 0.0 if no data.
        """
        # Load FM fire events (columns: Dist_Type_ID, Step, Amount)
        fm_events = self.loader.FM_disturbances_time_series()
        fm_fire = fm_events[fm_events["Dist_Type_ID"] == "DISTID3"]

        # Load AF fire events (same column names as FM in database)
        af_events = self.loader.AF_disturbances_time_series()
        af_fire = af_events[af_events["Dist_Type_ID"] == "DISTID3"]

        # Mean annual fire area for each pipeline
        if not fm_fire.empty:
            fm_mean_annual = fm_fire.groupby("Step")["Amount"].sum().mean()
        else:
            fm_mean_annual = 0.0

        if not af_fire.empty:
            af_mean_annual = af_fire.groupby("Step")["Amount"].sum().mean()
        else:
            af_mean_annual = 0.0

        combined_mean_annual_fire = fm_mean_annual + af_mean_annual

        # Total forest area from FM + AF inventories
        fm_area = self.loader.FM_inventory()["Area"].sum()
        af_area = self.loader.AF_inventory()["Area"].sum()
        total_area = fm_area + af_area

        if total_area <= 0:
            return 0.0

        return combined_mean_annual_fire / total_area

    def _create_fire_row(self, year, fire_area):
        """
        Create a DISTID3 fire event row with wildcard classifiers.

        Matches FM/AF fire format: all classifiers '?', SortType=6,
        MeasureType='A' (area-based).
        """
        static_defaults = {col: -1 for col in self.static_cols}

        return {
            "Classifier1": "?",
            "Classifier2": "?",
            "Classifier3": "?",
            "Classifier4": "?",
            "UsingID": False,
            "sw_age_min": 0,
            "sw_age_max": 210,
            "hw_age_min": 0,
            "hw_age_max": 210,
            "MinYearsSinceDist": -1,
            **static_defaults,
            "Efficiency": 1,
            "SortType": 6,
            "MeasureType": "A",
            "Amount": fire_area,
            "DistTypeID": "DISTID3",
            "Year": year,
        }
