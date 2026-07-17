"""
Loader Base Module
==================
Base class for component-specific loaders (AF, FM, SC).
Provides shared database connection and table reading functionality.
"""
import sqlalchemy as sqa
import pandas as pd
from goblin_cbm_runner.database import get_local_dir
import os


class LoaderBase:
    """
    Base class for CBM Runner loaders.

    Provides shared functionality for database access.
    Component-specific loaders (AFLoader, FMLoader, SCLoader) inherit from this.

    Attributes:
        database_dir (str): Directory containing the database file.
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine for database access.
    """

    def __init__(self, db_path=None):
        """
        Initialize the loader with database connection.

        Args:
            db_path (str, optional): Full path to database file.
                If None, uses default cbm_runner_database_0.6.2.db
        """
        self.database_dir = get_local_dir()

        if db_path:
            database_path = db_path
        else:
            database_path = os.path.abspath(
                os.path.join(self.database_dir, "cbm_runner_database_0.6.2.db")
            )

        engine_url = f"sqlite:///{database_path}"
        self.engine = sqa.create_engine(engine_url)

    def _read_table(self, table_name: str, index_col=None) -> pd.DataFrame:
        """
        Read a table from the database.

        Args:
            table_name (str): Name of the table to read.
            index_col (str, optional): Column to use as index.

        Returns:
            pd.DataFrame: Table contents as DataFrame.
        """
        if index_col:
            return pd.read_sql(
                f"SELECT * FROM '{table_name}'",
                self.engine,
                index_col=[index_col]
            )
        return pd.read_sql(
            f"SELECT * FROM '{table_name}'",
            self.engine
        )
