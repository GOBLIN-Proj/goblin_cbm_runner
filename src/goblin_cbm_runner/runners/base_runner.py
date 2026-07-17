"""
Base Runner
===========
Abstract base class for CBM runners.

All concrete implementations (AFRunner, FMRunner, SCRunner) must provide:
- generate_input_data(): Prepare SIT input files
- run_flux_scenarios(): Run CBM simulation and return flux results
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseRunner(ABC):
    """
    Abstract base class for CBM runners.

    Required methods for all runners:
    - generate_input_data(): Generate SIT CSV/JSON input files
    - run_flux_scenarios(): Run simulation, return flux DataFrame
    """

    @abstractmethod
    def generate_input_data(self) -> None:
        """
        Generate all necessary input data for the CBM simulation.

        Creates SIT-format files (CSV, JSON) in the configured input directory.
        """
        pass

    @abstractmethod
    def run_flux_scenarios(self) -> pd.DataFrame:
        """
        Run the CBM simulation and return flux results.

        Returns:
            DataFrame with carbon flux data indexed by Year.
        """
        pass