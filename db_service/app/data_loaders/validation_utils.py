"""
Utility functions for data validation and loading.
"""

import os
from sqlalchemy.orm import Session
from typing import Type, Union, List
from pathlib import Path


def should_reload_data(
    session: Session, 
    table_model: Type, 
    csv_file_path: Union[str, Path], 
    table_name: str,
    threshold_percent: float = 0.9
) -> bool:
    """
    Check if we should reload data based on CSV vs DB row counts.
    
    Args:
        session: SQLAlchemy database session
        table_model: SQLAlchemy model class for the table
        csv_file_path: Path to the CSV file to compare against
        table_name: Human-readable name for logging
        threshold_percent: Minimum percentage of CSV rows that should exist in DB (default 90%)
    
    Returns:
        bool: True if data should be reloaded, False if adequate data exists
    """
    if not os.path.exists(csv_file_path):
        print(f"   WARNING: {csv_file_path} not found, skipping {table_name} validation")
        return False
        
    # Count rows in CSV
    with open(csv_file_path, 'r') as f:
        csv_row_count = sum(1 for line in f) - 1  # Subtract header row
    
    # Count rows in database
    db_row_count = session.query(table_model).count()
    
    threshold = threshold_percent * csv_row_count
    should_reload = db_row_count < threshold
    
    print(f"{table_name}: CSV has {csv_row_count} rows, DB has {db_row_count} rows (threshold: {threshold:.0f})")
    if should_reload:
        print(f"   -> Will reload {table_name} (insufficient data in DB)")
        # Clear existing data
        session.query(table_model).delete()
        session.commit()
    else:
        print(f"   -> {table_name} already adequately populated")
        
    return should_reload


def should_reload_data_multiple_csvs(
    session: Session,
    table_model: Type,
    csv_file_paths: List[Union[str, Path]],
    table_name: str,
    threshold_percent: float = 0.9
) -> bool:
    """
    Check if we should reload data based on multiple CSV files vs DB row counts.
    Useful for cases like enriched products where data comes from multiple CSV files.
    
    Args:
        session: SQLAlchemy database session
        table_model: SQLAlchemy model class for the table
        csv_file_paths: List of paths to CSV files to compare against
        table_name: Human-readable name for logging
        threshold_percent: Minimum percentage of CSV rows that should exist in DB (default 90%)
    
    Returns:
        bool: True if data should be reloaded, False if adequate data exists
    """
    # Count total rows across all CSV files
    total_csv_rows = 0
    missing_files = []
    
    for csv_file_path in csv_file_paths:
        if not os.path.exists(csv_file_path):
            missing_files.append(str(csv_file_path))
            continue
            
        with open(csv_file_path, 'r') as f:
            csv_rows = sum(1 for line in f) - 1  # Subtract header row
            total_csv_rows += csv_rows
    
    if missing_files:
        print(f"   WARNING: Missing CSV files for {table_name}: {missing_files}")
    
    if total_csv_rows == 0:
        print(f"   WARNING: No valid CSV files found for {table_name}, skipping validation")
        return False
    
    # Count rows in database
    db_row_count = session.query(table_model).count()
    
    threshold = threshold_percent * total_csv_rows
    should_reload = db_row_count < threshold
    
    print(f"{table_name}: CSV files have {total_csv_rows} total rows, DB has {db_row_count} rows (threshold: {threshold:.0f})")
    if should_reload:
        print(f"   -> Will reload {table_name} (insufficient data in DB)")
        # Clear existing data
        from sqlalchemy import text
        session.execute(text(f"DELETE FROM {table_model.__table__.schema}.{table_model.__table__.name}"))
        session.commit()
    else:
        print(f"   -> {table_name} already adequately populated")
        
    return should_reload
