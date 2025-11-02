"""
NASA Turbofan Engine Degradation Dataset - Download and Preprocessing Script

This script downloads, preprocesses, and prepares the NASA CMAPSS Turbofan Engine
Degradation dataset for equipment failure prediction modeling.

Dataset: Commercial Modular Aero-Propulsion System Simulation (CMAPSS)
Source: NASA Prognostics Data Repository

Author: DRDO Development Team
Date: 2025-01-02
Version: 1.0
"""

import os
import sys
import json
import logging
import argparse
import zipfile
import requests
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tqdm import tqdm

warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

# Dataset URLs (multiple sources for redundancy)
DATASET_URLS = {
    'primary': 'https://ti.arc.nasa.gov/c/6/',  # NASA repository
    'mirror': 'https://phm-datasets.s3.amazonaws.com/NASA/4.+Turbofan+Engine+Degradation+Simulation.zip'
}

# Column names for CMAPSS dataset
COLUMN_NAMES = [
    'unit_id',           # Engine unit identifier
    'time_cycles',       # Operational cycle number
    'op_setting_1',      # Operational setting 1
    'op_setting_2',      # Operational setting 2  
    'op_setting_3',      # Operational setting 3
    'sensor_1',          # Temperature at fan inlet
    'sensor_2',          # Temperature at LPC outlet
    'sensor_3',          # Temperature at HPC outlet
    'sensor_4',          # Temperature at LPT outlet
    'sensor_5',          # Pressure at fan inlet
    'sensor_6',          # Pressure at LPC outlet
    'sensor_7',          # Pressure at HPC outlet
    'sensor_8',          # Physical fan speed
    'sensor_9',          # Physical core speed
    'sensor_10',         # Engine pressure ratio
    'sensor_11',         # Static pressure at HPC outlet
    'sensor_12',         # Ratio of fuel flow to Ps30
    'sensor_13',         # Corrected fan speed
    'sensor_14',         # Corrected core speed
    'sensor_15',         # Bypass Ratio
    'sensor_16',         # Burner fuel-air ratio
    'sensor_17',         # Bleed Enthalpy
    'sensor_18',         # Demanded fan speed
    'sensor_19',         # Demanded corrected fan speed
    'sensor_20',         # HPT coolant bleed
    'sensor_21'          # LPT coolant bleed
]

# Sensors to use for modeling (remove constant/unhelpful sensors)
USEFUL_SENSORS = [
    'sensor_2', 'sensor_3', 'sensor_4', 'sensor_7', 'sensor_8',
    'sensor_9', 'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14',
    'sensor_15', 'sensor_17', 'sensor_20', 'sensor_21'
]


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_dir: str, verbose: bool = False) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_dir: Directory to save log files
        verbose: If True, set log level to DEBUG
        
    Returns:
        Configured logger instance
    """
    os.makedirs(log_dir, exist_ok=True)
    
    log_level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'dataset_preparation_{timestamp}.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger


# ============================================================================
# DATASET DOWNLOAD
# ============================================================================

def download_dataset(
    url: str,
    output_path: str,
    logger: logging.Logger,
    max_retries: int = 3
) -> bool:
    """
    Download dataset from URL with retry logic and progress bar.
    
    Args:
        url: Dataset download URL
        output_path: Path to save downloaded file
        logger: Logger instance
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download successful, False otherwise
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries} from: {url}")
            
            # Send HEAD request to get file size
            response = requests.head(url, timeout=10, allow_redirects=True)
            file_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f, tqdm(
                desc="Downloading",
                total=file_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            logger.info(f"Download successful: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error("All download attempts failed")
                return False
            logger.info("Retrying...")
            
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False
    
    return False


def extract_dataset(zip_path: str, extract_to: str, logger: logging.Logger) -> bool:
    """
    Extract ZIP file to specified directory.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract files
        logger: Logger instance
        
    Returns:
        True if extraction successful, False otherwise
    """
    try:
        logger.info(f"Extracting ZIP file: {zip_path}")
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in archive")
            
            # Extract with progress bar
            for file in tqdm(file_list, desc="Extracting"):
                zip_ref.extract(file, extract_to)
        
        logger.info(f"Extraction complete: {extract_to}")
        return True
        
    except zipfile.BadZipFile:
        logger.error(f"Invalid ZIP file: {zip_path}")
        return False
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        return False


# ============================================================================
# DATA LOADING
# ============================================================================

def load_raw_data(
    file_path: str,
    column_names: List[str],
    logger: logging.Logger
) -> Optional[pd.DataFrame]:
    """
    Load raw data from text file into DataFrame.
    
    Args:
        file_path: Path to data file
        column_names: List of column names
        logger: Logger instance
        
    Returns:
        DataFrame with loaded data or None if error
    """
    try:
        logger.info(f"Loading data from: {file_path}")
        
        # Load space-separated data
        df = pd.read_csv(
            file_path,
            sep=r'\s+',
            header=None,
            names=column_names
        )
        
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
        return df
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None


# ============================================================================
# DATA PREPROCESSING
# ============================================================================

def preprocess_data(
    df: pd.DataFrame,
    useful_sensors: List[str],
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Clean and preprocess raw data.
    
    Args:
        df: Raw DataFrame
        useful_sensors: List of sensor columns to keep
        logger: Logger instance
        
    Returns:
        Preprocessed DataFrame
    """
    logger.info("Starting data preprocessing...")
    
    # Keep only useful columns
    keep_cols = ['unit_id', 'time_cycles'] + useful_sensors
    df_processed = df[keep_cols].copy()
    
    # Check for missing values
    missing = df_processed.isnull().sum()
    if missing.any():
        logger.warning(f"Missing values found:\n{missing[missing > 0]}")
        df_processed = df_processed.dropna()
        logger.info(f"Dropped rows with missing values. Remaining: {len(df_processed)}")
    else:
        logger.info("No missing values found")
    
    # Remove duplicate rows
    before_dup = len(df_processed)
    df_processed = df_processed.drop_duplicates()
    after_dup = len(df_processed)
    if before_dup != after_dup:
        logger.info(f"Removed {before_dup - after_dup} duplicate rows")
    
    # Sort by unit and cycle
    df_processed = df_processed.sort_values(['unit_id', 'time_cycles'])
    
    logger.info(f"Preprocessing complete. Shape: {df_processed.shape}")
    return df_processed


def calculate_rul(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Calculate Remaining Useful Life (RUL) for each engine unit.
    
    RUL = Maximum cycle number - Current cycle number
    
    Args:
        df: DataFrame with unit_id and time_cycles
        logger: Logger instance
        
    Returns:
        DataFrame with RUL column added
    """
    logger.info("Calculating Remaining Useful Life (RUL)...")
    
    # Get maximum cycle for each unit
    max_cycles = df.groupby('unit_id')['time_cycles'].max().reset_index()
    max_cycles.columns = ['unit_id', 'max_cycle']
    
    # Merge back to original dataframe
    df = df.merge(max_cycles, on='unit_id', how='left')
    
    # Calculate RUL
    df['RUL'] = df['max_cycle'] - df['time_cycles']
    
    # Drop intermediate column
    df = df.drop('max_cycle', axis=1)
    
    logger.info(f"RUL statistics:\n{df['RUL'].describe()}")
    return df


def create_failure_labels(
    df: pd.DataFrame,
    threshold: int,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Create binary failure labels based on RUL threshold.
    
    Label = 1 if failure imminent (RUL <= threshold)
    Label = 0 if normal operation (RUL > threshold)
    
    Args:
        df: DataFrame with RUL column
        threshold: RUL threshold for failure label (days/cycles)
        logger: Logger instance
        
    Returns:
        DataFrame with failure_label column
    """
    logger.info(f"Creating failure labels (threshold: {threshold} cycles)...")
    
    df['failure_label'] = (df['RUL'] <= threshold).astype(int)
    
    # Calculate class distribution
    label_counts = df['failure_label'].value_counts()
    total = len(df)
    
    logger.info(f"Label distribution:")
    logger.info(f"  Normal (0): {label_counts.get(0, 0):,} ({label_counts.get(0, 0)/total*100:.2f}%)")
    logger.info(f"  Failure (1): {label_counts.get(1, 0):,} ({label_counts.get(1, 0)/total*100:.2f}%)")
    
    return df


# ============================================================================
# FEATURE ENGINEERING
# ============================================================================

def engineer_features(
    df: pd.DataFrame,
    sensor_cols: List[str],
    window_size: int,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Create engineered features from raw sensor data.
    
    Features created:
    - Rolling mean (smoothed sensor values)
    - Rolling std (sensor variability)
    - Sensor differences (trends)
    - Interaction features
    
    Args:
        df: DataFrame with sensor columns
        sensor_cols: List of sensor column names
        window_size: Window size for rolling statistics
        logger: Logger instance
        
    Returns:
        DataFrame with engineered features
    """
    logger.info(f"Engineering features (window size: {window_size})...")
    
    # Create copy to avoid modifying original
    df_feat = df.copy()
    
    # Group by unit for time-series features
    for sensor in tqdm(sensor_cols, desc="Feature engineering"):
        # Rolling mean
        df_feat[f'{sensor}_rolling_mean'] = df_feat.groupby('unit_id')[sensor].transform(
            lambda x: x.rolling(window=window_size, min_periods=1).mean()
        )
        
        # Rolling standard deviation (variability)
        df_feat[f'{sensor}_rolling_std'] = df_feat.groupby('unit_id')[sensor].transform(
            lambda x: x.rolling(window=window_size, min_periods=1).std().fillna(0)
        )
        
        # Sensor difference (trend detection)
        df_feat[f'{sensor}_diff'] = df_feat.groupby('unit_id')[sensor].transform(
            lambda x: x.diff().fillna(0)
        )
    
    # Interaction features (selected combinations)
    df_feat['temp_vibration_interaction'] = df_feat['sensor_2'] * df_feat['sensor_8']
    df_feat['pressure_speed_interaction'] = df_feat['sensor_7'] * df_feat['sensor_9']
    
    # Fill any remaining NaN values from rolling operations
    df_feat = df_feat.fillna(method='bfill').fillna(0)
    
    logger.info(f"Feature engineering complete. New shape: {df_feat.shape}")
    logger.info(f"Total features: {len(df_feat.columns)}")
    
    return df_feat


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_features(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    exclude_cols: List[str],
    logger: logging.Logger
) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Normalize numerical features using StandardScaler.
    
    Args:
        train_df: Training DataFrame
        test_df: Testing DataFrame
        exclude_cols: Columns to exclude from normalization
        logger: Logger instance
        
    Returns:
        Tuple of (normalized_train, normalized_test, fitted_scaler)
    """
    logger.info("Normalizing features...")
    
    # Identify numerical columns to normalize
    numeric_cols = [
        col for col in train_df.columns
        if col not in exclude_cols and train_df[col].dtype in ['float64', 'int64']
    ]
    
    logger.info(f"Normalizing {len(numeric_cols)} numerical features")
    
    # Fit scaler on training data only
    scaler = StandardScaler()
    train_df[numeric_cols] = scaler.fit_transform(train_df[numeric_cols])
    
    # Transform test data using fitted scaler
    test_df[numeric_cols] = scaler.transform(test_df[numeric_cols])
    
    logger.info("Normalization complete")
    
    return train_df, test_df, scaler


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_data(
    df: pd.DataFrame,
    logger: logging.Logger
) -> Dict[str, any]:
    """
    Validate processed data quality.
    
    Args:
        df: DataFrame to validate
        logger: Logger instance
        
    Returns:
        Dictionary with validation results
    """
    logger.info("Validating data quality...")
    
    validation_results = {}
    
    # Check missing values
    missing_count = df.isnull().sum().sum()
    validation_results['missing_values'] = missing_count
    
    # Check duplicates
    dup_count = df.duplicated().sum()
    validation_results['duplicates'] = dup_count
    
    # Check label distribution
    if 'failure_label' in df.columns:
        label_dist = df['failure_label'].value_counts().to_dict()
        validation_results['label_distribution'] = label_dist
    
    # Check for infinite values
    inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
    validation_results['infinite_values'] = inf_count
    
    # Feature ranges
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    ranges = {}
    for col in numeric_cols:
        ranges[col] = {
            'min': float(df[col].min()),
            'max': float(df[col].max()),
            'mean': float(df[col].mean())
        }
    validation_results['feature_ranges'] = ranges
    
    # Log warnings
    if missing_count > 0:
        logger.warning(f"Found {missing_count} missing values")
    if dup_count > 0:
        logger.warning(f"Found {dup_count} duplicate rows")
    if inf_count > 0:
        logger.warning(f"Found {inf_count} infinite values")
    
    logger.info("Data validation complete")
    
    return validation_results


# ============================================================================
# SAVE OUTPUTS
# ============================================================================

def save_processed_data(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    scaler: StandardScaler,
    output_dir: str,
    logger: logging.Logger
) -> None:
    """
    Save processed data in multiple formats.
    
    Args:
        train_df: Processed training DataFrame
        test_df: Processed testing DataFrame
        scaler: Fitted StandardScaler
        output_dir: Output directory
        logger: Logger instance
    """
    logger.info(f"Saving processed data to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save CSV files
    train_csv = os.path.join(output_dir, 'train_preprocessed.csv')
    test_csv = os.path.join(output_dir, 'test_preprocessed.csv')
    
    train_df.to_csv(train_csv, index=False)
    test_df.to_csv(test_csv, index=False)
    logger.info(f"Saved CSV files: {train_csv}, {test_csv}")
    
    # Prepare feature arrays (exclude metadata columns)
    exclude_cols = ['unit_id', 'time_cycles', 'RUL', 'failure_label']
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    
    train_features = train_df[feature_cols].values
    test_features = test_df[feature_cols].values
    
    # Save numpy arrays
    train_npy = os.path.join(output_dir, 'train_features.npy')
    test_npy = os.path.join(output_dir, 'test_features.npy')
    
    np.save(train_npy, train_features)
    np.save(test_npy, test_features)
    logger.info(f"Saved numpy arrays: {train_npy}, {test_npy}")
    
    # Save labels separately
    train_labels = train_df['failure_label'].values
    test_labels = test_df['failure_label'].values
    
    np.save(os.path.join(output_dir, 'train_labels.npy'), train_labels)
    np.save(os.path.join(output_dir, 'test_labels.npy'), test_labels)
    logger.info("Saved label arrays")
    
    # Save scaler
    import joblib
    scaler_path = os.path.join(output_dir, 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    logger.info(f"Saved scaler: {scaler_path}")
    
    # Save feature names
    feature_names_path = os.path.join(output_dir, 'feature_names.json')
    with open(feature_names_path, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    logger.info(f"Saved feature names: {feature_names_path}")


def generate_report(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    validation_results: Dict,
    output_dir: str,
    logger: logging.Logger
) -> None:
    """
    Generate comprehensive data quality report.
    
    Args:
        train_df: Training DataFrame
        test_df: Testing DataFrame
        validation_results: Dictionary with validation results
        output_dir: Output directory
        logger: Logger instance
    """
    logger.info("Generating data quality report...")
    
    report_path = os.path.join(output_dir, 'data_quality_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("NASA TURBOFAN ENGINE DEGRADATION DATASET - DATA QUALITY REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Dataset summary
        f.write("DATASET SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total samples: {len(train_df) + len(test_df):,}\n")
        f.write(f"Training samples: {len(train_df):,} ({len(train_df)/(len(train_df)+len(test_df))*100:.1f}%)\n")
        f.write(f"Testing samples: {len(test_df):,} ({len(test_df)/(len(train_df)+len(test_df))*100:.1f}%)\n")
        f.write(f"Number of features: {len([c for c in train_df.columns if c not in ['unit_id', 'time_cycles', 'RUL', 'failure_label']])}\n")
        f.write(f"Number of engine units (train): {train_df['unit_id'].nunique()}\n")
        f.write(f"Number of engine units (test): {test_df['unit_id'].nunique()}\n\n")
        
        # Label distribution
        f.write("LABEL DISTRIBUTION\n")
        f.write("-" * 80 + "\n")
        train_labels = train_df['failure_label'].value_counts()
        f.write(f"Training set:\n")
        f.write(f"  Normal (0): {train_labels.get(0, 0):,} ({train_labels.get(0, 0)/len(train_df)*100:.2f}%)\n")
        f.write(f"  Failure (1): {train_labels.get(1, 0):,} ({train_labels.get(1, 0)/len(train_df)*100:.2f}%)\n\n")
        
        test_labels = test_df['failure_label'].value_counts()
        f.write(f"Testing set:\n")
        f.write(f"  Normal (0): {test_labels.get(0, 0):,} ({test_labels.get(0, 0)/len(test_df)*100:.2f}%)\n")
        f.write(f"  Failure (1): {test_labels.get(1, 0):,} ({test_labels.get(1, 0)/len(test_df)*100:.2f}%)\n\n")
        
        # Data quality
        f.write("DATA QUALITY CHECKS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Missing values: {validation_results.get('missing_values', 0)}\n")
        f.write(f"Duplicate rows: {validation_results.get('duplicates', 0)}\n")
        f.write(f"Infinite values: {validation_results.get('infinite_values', 0)}\n\n")
        
        # Feature statistics
        f.write("FEATURE VALUE RANGES (Training Set)\n")
        f.write("-" * 80 + "\n")
        feature_ranges = validation_results.get('feature_ranges', {})
        for feature, stats in list(feature_ranges.items())[:10]:  # Show first 10
            f.write(f"{feature}:\n")
            f.write(f"  Min: {stats['min']:.4f}, Max: {stats['max']:.4f}, Mean: {stats['mean']:.4f}\n")
        
        if len(feature_ranges) > 10:
            f.write(f"... and {len(feature_ranges) - 10} more features\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Report complete. Dataset ready for model training.\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Report saved: {report_path}")


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main(args: argparse.Namespace) -> None:
    """
    Main orchestration function.
    
    Args:
        args: Command-line arguments
    """
    # Setup logging
    logger = setup_logging(args.log_dir, args.verbose)
    logger.info("=" * 80)
    logger.info("NASA TURBOFAN DATASET PREPARATION - STARTED")
    logger.info("=" * 80)
    
    try:
        # Create directories
        raw_dir = os.path.join(args.data_dir, 'raw')
        processed_dir = os.path.join(args.data_dir, 'processed')
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        # Step 1: Download dataset
        if args.download:
            zip_path = os.path.join(raw_dir, 'cmapss_data.zip')
            
            if not os.path.exists(zip_path):
                logger.info("Step 1/8: Downloading dataset...")
                # Try primary URL first, then mirror
                success = download_dataset(
                    DATASET_URLS['primary'],
                    zip_path,
                    logger,
                    max_retries=args.max_retries
                )
                
                if not success:
                    logger.info("Trying mirror URL...")
                    success = download_dataset(
                        DATASET_URLS['mirror'],
                        zip_path,
                        logger,
                        max_retries=args.max_retries
                    )
                
                if not success:
                    logger.error("Failed to download dataset from all sources")
                    logger.info("Please download manually from:")
                    logger.info("  https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/")
                    return
            else:
                logger.info(f"Dataset already downloaded: {zip_path}")
            
            # Extract dataset
            logger.info("Step 2/8: Extracting dataset...")
            if not extract_dataset(zip_path, raw_dir, logger):
                logger.error("Failed to extract dataset")
                return
        
        # Step 3: Load raw data
        logger.info("Step 3/8: Loading raw data...")
        
        # For this example, we'll use FD001 (first subset)
        train_file = os.path.join(raw_dir, 'train_FD001.txt')
        test_file = os.path.join(raw_dir, 'test_FD001.txt')
        
        # Check if files exist
        if not os.path.exists(train_file):
            logger.error(f"Training file not found: {train_file}")
            logger.info("Please ensure the CMAPSS dataset files are in the raw directory")
            return
        
        train_raw = load_raw_data(train_file, COLUMN_NAMES, logger)
        test_raw = load_raw_data(test_file, COLUMN_NAMES, logger)
        
        if train_raw is None or test_raw is None:
            logger.error("Failed to load raw data")
            return
        
        # Step 4: Preprocess data
        logger.info("Step 4/8: Preprocessing data...")
        train_clean = preprocess_data(train_raw, USEFUL_SENSORS, logger)
        test_clean = preprocess_data(test_raw, USEFUL_SENSORS, logger)
        
        # Step 5: Calculate RUL and create labels
        logger.info("Step 5/8: Calculating RUL and creating labels...")
        train_rul = calculate_rul(train_clean, logger)
        test_rul = calculate_rul(test_clean, logger)
        
        train_labeled = create_failure_labels(train_rul, args.failure_threshold, logger)
        test_labeled = create_failure_labels(test_rul, args.failure_threshold, logger)
        
        # Step 6: Feature engineering
        logger.info("Step 6/8: Engineering features...")
        train_feat = engineer_features(train_labeled, USEFUL_SENSORS, args.window_size, logger)
        test_feat = engineer_features(test_labeled, USEFUL_SENSORS, args.window_size, logger)
        
        # Step 7: Normalize features
        logger.info("Step 7/8: Normalizing features...")
        exclude_from_norm = ['unit_id', 'time_cycles', 'RUL', 'failure_label']
        train_norm, test_norm, scaler = normalize_features(
            train_feat, test_feat, exclude_from_norm, logger
        )
        
        # Step 8: Validate and save
        logger.info("Step 8/8: Validating and saving data...")
        validation_results = validate_data(train_norm, logger)
        
        save_processed_data(train_norm, test_norm, scaler, processed_dir, logger)
        
        generate_report(train_norm, test_norm, validation_results, processed_dir, logger)
        
        logger.info("=" * 80)
        logger.info("DATASET PREPARATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Processed data saved to: {processed_dir}")
        logger.info(f"Training samples: {len(train_norm):,}")
        logger.info(f"Testing samples: {len(test_norm):,}")
        logger.info(f"Total features: {len([c for c in train_norm.columns if c not in exclude_from_norm])}")
        
    except Exception as e:
        logger.error(f"Fatal error during dataset preparation: {e}", exc_info=True)
        raise


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download and prepare NASA Turbofan Engine Degradation dataset',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./data',
        help='Root directory for data storage'
    )
    
    parser.add_argument(
        '--log-dir',
        type=str,
        default='./logs',
        help='Directory for log files'
    )
    
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download dataset from source'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum download retry attempts'
    )
    
    parser.add_argument(
        '--failure-threshold',
        type=int,
        default=30,
        help='RUL threshold for failure label (cycles)'
    )
    
    parser.add_argument(
        '--window-size',
        type=int,
        default=5,
        help='Window size for rolling features'
    )
    
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    args = parser.parse_args()
    
    # Set random seed
    np.random.seed(args.random_seed)
    
    # Run main process
    main(args)
