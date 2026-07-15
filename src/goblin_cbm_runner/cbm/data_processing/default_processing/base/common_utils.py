"""
Common Utilities for Data Generators
=====================================
Shared utility functions used across AF, FM, and SC generators.
"""
import os
import shutil
import pandas as pd
from typing import List


def ensure_directory_exists(path: str) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to check/create
    """
    os.makedirs(path, exist_ok=True)


def clean_directory(path: str) -> None:
    """
    Remove all files from directory if it exists.

    Args:
        path: Directory path to clean
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def save_dataframe_csv(df: pd.DataFrame, output_path: str, filename: str) -> None:
    """
    Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        output_path: Directory path
        filename: CSV filename (e.g., 'inventory.csv')
    """
    ensure_directory_exists(output_path)
    filepath = os.path.join(output_path, filename)
    df.to_csv(filepath, index=False)


def get_classifier_columns(df: pd.DataFrame) -> List[str]:
    """
    Extract all classifier column names from a DataFrame.

    Args:
        df: DataFrame to extract from

    Returns:
        List of column names starting with 'Classifier'
    """
    return [col for col in df.columns if 'Classifier' in col]
