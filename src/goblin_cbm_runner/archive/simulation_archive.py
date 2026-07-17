"""
Simulation Archive
==================
SQLite-based archive for simulation inputs and results.

Provides:
- Store all input files (inventory, disturbances, etc.) with scenario ID and runner type
- Store individual and combined results
- Store validation tables (pools, flux, state, etc.) from comprehensive simulations
- Metadata storage: run configuration, timestamps
- Export capability: copy archive to user-specified location

Users can query the archive with any SQLite tool or library.

Usage:
    archive = SimulationArchive(path="./my_archive.db")

    # Store input files for a runner
    archive.store_scenario_inputs(
        scenario=0,
        runner_type='SC',
        data={
            'inventory': inventory_df,
            'disturbance_events': disturbance_df,
        }
    )

    # Store results
    archive.store_results(
        scenario=0,
        runner_type='SC',
        results=flux_df
    )

    # Store validation tables from comprehensive simulation
    archive.store_validation_tables(
        scenario=-1,
        runner_type='AF',
        tables={
            'pools': pools_df,
            'flux': flux_df,
            'state': state_df,
            ...
        }
    )

    # Create reference table mapping our names to CBM-CFS3 names
    archive.store_table_map()

    # Export to permanent location
    archive.export_to("/path/to/saved_archive.db")

    # User queries externally with any SQLite tool:
    # SELECT * FROM _cbm_table_map  -- See table name mappings
    # SELECT * FROM AF_validation_pools WHERE scenario = -1
    # SELECT * FROM results WHERE runner_type = 'AF'
"""
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from typing import Dict, Optional, Any
import json

import pandas as pd


# Mapping of our validation table names to Kevin Black's CBM-CFS3 equivalents
# This is stored in the archive as _cbm_table_map for self-documentation
CBM_TABLE_MAP = {
    'pools': ('tblPoolIndicator', 'Carbon pools per stand per timestep (SoftwoodMerch, HardwoodMerch, etc.)'),
    'flux': ('tblFluxIndicators', 'Carbon fluxes per stand per timestep (DisturbanceSoftProduction, etc.)'),
    'state': ('tblDisturbanceIndicators', 'Stand state: age, last_disturbance_type, land_class'),
    'area': ('area_tracking', 'Stand areas per timestep'),
    'parameters': ('disturbance_parameters', 'Disturbance parameters applied to each stand'),
    'classifiers': ('tblUserDefdClasses', 'Classifier values per stand: species (Classifier1), soil, etc.'),
}


class SimulationArchive:
    """
    SQLite archive for simulation inputs and results.

    All tables get 'scenario' and 'runner_type' columns added automatically.
    Runner types: 'AF', 'FM', 'SC', 'combined_af_fm', 'combined_sc_af_fm',
                  'dynamic_FM', 'dynamic_AF'

    Table Types:
        Input tables: {runner_type}_{table_name}
            e.g., AF_inventory, FM_disturbance_events, SC_classifiers

        Results table: results
            Contains aggregated carbon stocks with 'runner_type' column

        Validation tables: {runner_type}_validation_{table_name}
            e.g., AF_validation_pools, FM_validation_flux
            These map to Kevin Black's CBM-CFS3 output tables

        Reference table: _cbm_table_map
            Maps our table names to CBM-CFS3 equivalents

    Key Methods:
        store_scenario_inputs(): Store SIT input files
        store_results(): Store aggregated simulation results
        store_validation_tables(): Store detailed validation tables
        store_table_map(): Create CBM-CFS3 naming reference

    Attributes:
        path (str): Path to the SQLite database file
        conn (sqlite3.Connection): Database connection
    """

    def __init__(self, path: Optional[str] = None):
        """
        Initialize the archive.

        Args:
            path: Path to create/open SQLite database.
                  If None, creates a temporary file.
                  If file exists, it will be overwritten (fresh archive per run).
        """
        if path is None:
            # Create temp file that persists until explicitly deleted
            fd, path = tempfile.mkstemp(suffix='.db', prefix='cbm_archive_')
            os.close(fd)

        self.path = path

        # Remove existing file for fresh start
        if os.path.exists(self.path):
            os.remove(self.path)

        # Create connection
        self.conn = sqlite3.connect(self.path)

        # Initialize metadata table
        self._init_metadata_table()

        # Track which tables have been created
        self._tables_created = set()

    def _init_metadata_table(self):
        """Create the metadata table for run information."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _run_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                config_json TEXT,
                notes TEXT
            )
        """)

        # Store creation timestamp
        self.conn.execute(
            "INSERT INTO _run_metadata (created_at) VALUES (?)",
            (datetime.now().isoformat(),)
        )
        self.conn.commit()

    def store_scenario_inputs(
        self,
        scenario: int,
        runner_type: str,
        data: Dict[str, pd.DataFrame]
    ):
        """
        Archive input DataFrames for a scenario.

        Each DataFrame is stored in a table named {runner_type}_{table_name}
        (e.g., AF_inventory, FM_disturbance_events, SC_classifiers).
        This keeps different runner schemas separate while allowing filtering.

        'scenario' column is automatically added.

        Args:
            scenario: Scenario number (e.g., -1, 0, 1, 2)
            runner_type: Runner type ('AF', 'FM', 'SC')
            data: Dict of {table_name: DataFrame}

        Example:
            archive.store_scenario_inputs(
                scenario=0,
                runner_type='SC',
                data={
                    'inventory': inventory_df,  # Stored as SC_inventory
                    'disturbance_events': disturbance_df,  # Stored as SC_disturbance_events
                }
            )

        Query examples:
            SELECT * FROM AF_inventory WHERE scenario = -1
            SELECT * FROM SC_disturbance_events WHERE scenario = 0
        """
        for table_name, df in data.items():
            if df is None or df.empty:
                continue

            # Prefix table name with runner type
            full_table_name = f"{runner_type}_{table_name}"

            # Add scenario column
            df_with_meta = df.copy()
            df_with_meta.insert(0, 'scenario', scenario)

            # Store to SQLite (creates table if needed, appends rows)
            df_with_meta.to_sql(
                full_table_name,
                self.conn,
                if_exists='append',
                index=False
            )

            self._tables_created.add(full_table_name)

        self.conn.commit()

    def store_results(
        self,
        scenario: int,
        runner_type: str,
        results: pd.DataFrame,
        table_name: str = 'results'
    ):
        """
        Store simulation results.

        Args:
            scenario: Scenario number (e.g., -1, 0, 1, 2)
            runner_type: Runner type ('AF', 'FM', 'SC', 'combined_af_fm', 'combined_sc_af_fm')
            results: Results DataFrame
            table_name: Table name (default: 'results')
        """
        if results is None or results.empty:
            return

        df_with_meta = results.copy()

        # Normalize column names to lowercase for checking
        cols_lower = [c.lower() for c in df_with_meta.columns]

        # Add scenario if not already present (check case-insensitive)
        if 'scenario' not in cols_lower:
            df_with_meta.insert(0, 'scenario', scenario)
        else:
            # Rename 'Scenario' to 'scenario' if needed for consistency
            for col in df_with_meta.columns:
                if col.lower() == 'scenario' and col != 'scenario':
                    df_with_meta = df_with_meta.rename(columns={col: 'scenario'})
                    break

        # Add runner_type if not already present
        cols_lower = [c.lower() for c in df_with_meta.columns]
        if 'runner_type' not in cols_lower:
            # Find position after scenario
            scenario_pos = list(df_with_meta.columns).index('scenario')
            df_with_meta.insert(scenario_pos + 1, 'runner_type', runner_type)

        df_with_meta.to_sql(
            table_name,
            self.conn,
            if_exists='append',
            index=False
        )

        self._tables_created.add(table_name)
        self.conn.commit()

    def store_dataframe(
        self,
        table_name: str,
        df: pd.DataFrame,
        scenario: Optional[int] = None,
        runner_type: Optional[str] = None
    ):
        """
        Store a single DataFrame to a table.

        Args:
            table_name: Name for the table
            df: DataFrame to store
            scenario: Optional scenario number
            runner_type: Optional runner type
        """
        if df is None or df.empty:
            return

        df_to_store = df.copy()

        if scenario is not None:
            df_to_store.insert(0, 'scenario', scenario)
        if runner_type is not None:
            insert_pos = 1 if scenario is not None else 0
            df_to_store.insert(insert_pos, 'runner_type', runner_type)

        df_to_store.to_sql(
            table_name,
            self.conn,
            if_exists='append',
            index=False
        )

        self._tables_created.add(table_name)
        self.conn.commit()

    def store_metadata(self, config: Optional[Dict[str, Any]] = None, notes: Optional[str] = None):
        """
        Store run metadata (configuration, notes).

        Args:
            config: Configuration dictionary (will be JSON serialized)
            notes: Free-text notes about the run
        """
        config_json = json.dumps(config) if config else None

        self.conn.execute(
            "UPDATE _run_metadata SET config_json = ?, notes = ? WHERE id = 1",
            (config_json, notes)
        )
        self.conn.commit()

    def store_validation_tables(
        self,
        scenario: int,
        runner_type: str,
        tables: Dict[str, pd.DataFrame]
    ):
        """
        Store validation tables from comprehensive simulation.

        Tables are stored as {runner_type}_validation_{table_name}
        (e.g., AF_validation_pools, FM_validation_flux, SC_validation_state).

        These tables map to Kevin Black's CBM-CFS3 output tables:
        - pools → tblPoolIndicator
        - flux → tblFluxIndicators
        - state → tblDisturbanceIndicators
        - area → area tracking
        - parameters → disturbance parameters
        - classifiers → tblUserDefdClasses

        Args:
            scenario: Scenario number (e.g., -1 for baseline, 0+ for scenarios)
            runner_type: Runner type ('AF', 'FM', 'SC')
            tables: Dict of {table_name: DataFrame} from comprehensive simulation
                    Expected keys: 'pools', 'flux', 'state', 'area', 'parameters', 'classifiers'

        Example:
            archive.store_validation_tables(
                scenario=-1,
                runner_type='AF',
                tables={
                    'pools': pools_df,
                    'flux': flux_df,
                    'state': state_df,
                    'area': area_df,
                    'parameters': parameters_df,
                    'classifiers': classifiers_df,
                }
            )

        Query examples:
            SELECT * FROM AF_validation_pools WHERE scenario = -1
            SELECT * FROM SC_validation_flux WHERE scenario = 0
        """
        for table_name, df in tables.items():
            if df is None or df.empty:
                continue

            # Create table name: {runner_type}_validation_{table_name}
            full_table_name = f"{runner_type}_validation_{table_name}"

            # Add scenario column
            df_with_meta = df.copy()
            df_with_meta.insert(0, 'scenario', scenario)

            # Store to SQLite
            df_with_meta.to_sql(
                full_table_name,
                self.conn,
                if_exists='append',
                index=False
            )

            self._tables_created.add(full_table_name)

        self.conn.commit()

    def store_table_map(self):
        """
        Create the _cbm_table_map reference table in the archive.

        This table documents the mapping between our validation table names
        and Kevin Black's CBM-CFS3 table names, making the archive self-documenting.

        The table contains:
        - our_table_name: Our naming convention (e.g., 'pools', 'flux')
        - cbm_cfs3_name: Kevin's CBM-CFS3 equivalent (e.g., 'tblPoolIndicator')
        - description: What the table contains
        - archive_pattern: How tables are named in archive (e.g., '{RT}_validation_pools')

        Query example:
            SELECT * FROM _cbm_table_map
        """
        # Build the mapping data
        map_data = []
        for our_name, (cbm_name, description) in CBM_TABLE_MAP.items():
            map_data.append({
                'our_table_name': our_name,
                'cbm_cfs3_name': cbm_name,
                'description': description,
                'archive_pattern': f'{{runner_type}}_validation_{our_name}',
            })

        map_df = pd.DataFrame(map_data)

        # Store to archive (replace if exists)
        map_df.to_sql(
            '_cbm_table_map',
            self.conn,
            if_exists='replace',
            index=False
        )

        self._tables_created.add('_cbm_table_map')
        self.conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """
        Get the SQLite connection for custom queries.

        Returns:
            sqlite3.Connection: Database connection
        """
        return self.conn

    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            sql: SQL query string

        Returns:
            DataFrame with query results
        """
        return pd.read_sql(sql, self.conn)

    def list_tables(self) -> list:
        """
        List all tables in the archive.

        Returns:
            List of table names
        """
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_scenarios(self) -> list:
        """
        Get list of scenarios stored in the archive.

        Returns:
            List of scenario numbers
        """
        # Try to get from any data table
        for table in self._tables_created:
            try:
                cursor = self.conn.execute(f"SELECT DISTINCT scenario FROM {table} ORDER BY scenario")
                return [row[0] for row in cursor.fetchall()]
            except sqlite3.Error:
                continue
        return []

    def export_to(self, destination: str):
        """
        Export the archive to a specified location.

        Args:
            destination: Path where to copy the archive file
        """
        # Ensure all changes are written
        self.conn.commit()

        # Close and reopen to ensure file is complete
        self.conn.close()

        # Copy file
        shutil.copy(self.path, destination)

        # Reopen connection
        self.conn = sqlite3.connect(self.path)

    def get_path(self) -> str:
        """Get the path to the archive file."""
        return self.path

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
        return False

    def __del__(self):
        """Destructor - ensure connection is closed."""
        self.close()
