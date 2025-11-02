# NASA Turbofan Dataset Preparation Guide

## Overview

The `download_and_prepare_dataset.py` script automates the entire process of downloading, preprocessing, and preparing the NASA CMAPSS Turbofan Engine Degradation dataset for machine learning model training.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy scikit-learn requests tqdm joblib
```

### 2. Basic Usage (Manual Data)

If you already have the CMAPSS dataset files:

```bash
# Place train_FD001.txt and test_FD001.txt in data/raw/ directory
python scripts/download_and_prepare_dataset.py
```

### 3. Download and Process

To download the dataset automatically:

```bash
python scripts/download_and_prepare_dataset.py --download --verbose
```

---

## Command-Line Options

### Required Options

None - all options have sensible defaults

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--data-dir` | `./data` | Root directory for data storage |
| `--log-dir` | `./logs` | Directory for log files |
| `--download` | `False` | Download dataset from NASA repository |
| `--max-retries` | `3` | Maximum download retry attempts |
| `--failure-threshold` | `30` | RUL threshold for failure label (cycles) |
| `--window-size` | `5` | Window size for rolling features |
| `--random-seed` | `42` | Random seed for reproducibility |
| `--verbose` | `False` | Enable verbose (DEBUG) logging |

---

## Usage Examples

### Example 1: Default Processing

Process existing dataset files with default settings:

```bash
python scripts/download_and_prepare_dataset.py
```

**Output:**
- `data/processed/train_preprocessed.csv`
- `data/processed/test_preprocessed.csv`
- `data/processed/train_features.npy`
- `data/processed/test_features.npy`
- `data/processed/train_labels.npy`
- `data/processed/test_labels.npy`
- `data/processed/scaler.pkl`
- `data/processed/feature_names.json`
- `data/processed/data_quality_report.txt`

### Example 2: Download and Process with Custom Parameters

```bash
python scripts/download_and_prepare_dataset.py \
  --download \
  --data-dir ./my_data \
  --failure-threshold 40 \
  --window-size 10 \
  --verbose
```

This will:
- Download dataset automatically
- Use custom data directory
- Label failures when RUL ≤ 40 cycles (instead of 30)
- Use window size of 10 for rolling features
- Enable verbose logging

### Example 3: Production Use

For production environments with comprehensive logging:

```bash
python scripts/download_and_prepare_dataset.py \
  --data-dir /data/production \
  --log-dir /logs/dataset_prep \
  --failure-threshold 30 \
  --window-size 5 \
  --random-seed 42 \
  --verbose
```

---

## Output Files

### CSV Files

**train_preprocessed.csv** and **test_preprocessed.csv**
- Complete preprocessed datasets with all features
- Includes metadata columns: `unit_id`, `time_cycles`, `RUL`
- Includes target: `failure_label`
- All features normalized

### NumPy Arrays

**train_features.npy** and **test_features.npy**
- Pure feature matrices (no metadata)
- Shape: (n_samples, n_features)
- Ready for direct model input

**train_labels.npy** and **test_labels.npy**
- Binary labels (0 = normal, 1 = failure)
- Shape: (n_samples,)

### Model Artifacts

**scaler.pkl**
- Fitted StandardScaler object
- Use for transforming new data: `scaler.transform(new_data)`

**feature_names.json**
- List of feature column names in order
- Maps to columns in feature arrays

### Reports

**data_quality_report.txt**
- Dataset statistics
- Label distribution
- Feature ranges
- Data quality checks

---

## Script Workflow

The script executes these steps in order:

### Step 1: Download Dataset (Optional)
- Downloads CMAPSS dataset from NASA repository
- Includes retry logic with progress bars
- Falls back to mirror URL if primary fails

### Step 2: Extract Dataset
- Extracts ZIP file to raw data directory
- Validates extracted files

### Step 3: Load Raw Data
- Loads train_FD001.txt and test_FD001.txt
- Applies column names
- Validates data structure

### Step 4: Preprocess Data
- Removes unhelpful sensors
- Checks for missing values
- Removes duplicates
- Sorts by unit and cycle

### Step 5: Calculate RUL and Labels
- Calculates Remaining Useful Life for each unit
- Creates binary failure labels based on threshold
- Logs class distribution

### Step 6: Feature Engineering
- Creates rolling mean features (smoothed sensors)
- Creates rolling std features (variability)
- Creates difference features (trends)
- Creates interaction features

### Step 7: Normalize Features
- Fits StandardScaler on training data
- Transforms both train and test data
- Preserves metadata columns

### Step 8: Validate and Save
- Validates data quality
- Saves all output files
- Generates comprehensive report

---

## Understanding the Output

### Label Distribution

Example from report:

```
LABEL DISTRIBUTION
--------------------------------------------------------------------------------
Training set:
  Normal (0): 16,631 (82.41%)
  Failure (1): 3,551 (17.59%)

Testing set:
  Normal (0): 11,534 (87.82%)
  Failure (1): 1,601 (12.18%)
```

**Interpretation:**
- Dataset is imbalanced (more normal than failure cases)
- Consider using class weights or sampling techniques in model training
- Failure threshold of 30 cycles captures ~15-18% of data as positive class

### Feature Engineering

The script creates 3 types of features for each sensor:

1. **Rolling Mean**: `sensor_X_rolling_mean`
   - Smoothed sensor values
   - Reduces noise
   - Window size: 5 cycles (default)

2. **Rolling Std**: `sensor_X_rolling_std`
   - Sensor variability
   - Detects unstable behavior
   - Higher values indicate erratic readings

3. **Difference**: `sensor_X_diff`
   - Trend detection
   - Captures rate of change
   - Positive = increasing, Negative = decreasing

4. **Interaction Features**:
   - `temp_vibration_interaction`: Temperature × Vibration
   - `pressure_speed_interaction`: Pressure × Speed

**Total Features**: 14 sensors × 4 feature types + 2 interactions = **58 features**

---

## Loading Processed Data

### Python Example

```python
import numpy as np
import pandas as pd
import joblib

# Load CSV (includes metadata)
train_df = pd.read_csv('data/processed/train_preprocessed.csv')
test_df = pd.read_csv('data/processed/test_preprocessed.csv')

# OR load NumPy arrays (features only)
X_train = np.load('data/processed/train_features.npy')
y_train = np.load('data/processed/train_labels.npy')

X_test = np.load('data/processed/test_features.npy')
y_test = np.load('data/processed/test_labels.npy')

# Load scaler for future transformations
scaler = joblib.load('data/processed/scaler.pkl')

# Load feature names
import json
with open('data/processed/feature_names.json', 'r') as f:
    feature_names = json.load(f)

print(f"Training shape: {X_train.shape}")
print(f"Features: {len(feature_names)}")
print(f"Failure rate: {y_train.mean():.2%}")
```

---

## Troubleshooting

### Issue: Download Fails

**Error:** `All download attempts failed`

**Solutions:**
1. Check internet connection
2. Try mirror URL
3. Download manually from: https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/
4. Place ZIP file in `data/raw/` directory

### Issue: File Not Found

**Error:** `Training file not found: data/raw/train_FD001.txt`

**Solutions:**
1. Download dataset using `--download` flag
2. Manually place CMAPSS files in `data/raw/` directory
3. Check file names match exactly: `train_FD001.txt`, `test_FD001.txt`

### Issue: Memory Error

**Error:** `MemoryError` during feature engineering

**Solutions:**
1. Reduce window size: `--window-size 3`
2. Process smaller subsets (modify script)
3. Use server with more RAM
4. Process in batches

### Issue: Imbalanced Labels

**Warning:** `Label distribution highly imbalanced`

**Solutions:**
1. Adjust failure threshold: `--failure-threshold 40` (more failures)
2. Use class weights in model training: `class_weight='balanced'`
3. Apply SMOTE or other sampling techniques
4. Use appropriate metrics (F1, precision-recall)

---

## Advanced Usage

### Processing Multiple Subsets

The CMAPSS dataset has 4 subsets (FD001, FD002, FD003, FD004). To process all:

```python
# Modify the main() function in the script
subsets = ['FD001', 'FD002', 'FD003', 'FD004']

for subset in subsets:
    train_file = os.path.join(raw_dir, f'train_{subset}.txt')
    test_file = os.path.join(raw_dir, f'test_{subset}.txt')
    
    # Process each subset...
    # Save to separate directories: processed/FD001/, etc.
```

### Custom Feature Engineering

Add your own features by modifying the `engineer_features()` function:

```python
# Add cumulative features
df_feat['sensor_2_cumsum'] = df_feat.groupby('unit_id')['sensor_2'].cumsum()

# Add exponential moving average
df_feat['sensor_3_ewm'] = df_feat.groupby('unit_id')['sensor_3'].transform(
    lambda x: x.ewm(span=5).mean()
)

# Add lag features
df_feat['sensor_4_lag1'] = df_feat.groupby('unit_id')['sensor_4'].shift(1)
```

### Changing Failure Definition

Modify the `create_failure_labels()` function for different definitions:

```python
# Multi-class labels (normal, warning, critical)
df['failure_label'] = pd.cut(
    df['RUL'], 
    bins=[-1, 15, 30, float('inf')],
    labels=[2, 1, 0]  # 2=critical, 1=warning, 0=normal
)
```

---

## Integration with Model Training

### Example: Train Random Forest

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Load processed data
X_train = np.load('data/processed/train_features.npy')
y_train = np.load('data/processed/train_labels.npy')
X_test = np.load('data/processed/test_features.npy')
y_test = np.load('data/processed/test_labels.npy')

# Train model with class weights for imbalance
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model
import joblib
joblib.dump(model, 'models/failure_predictor_v1.pkl')
```

---

## Performance Benchmarks

Typical execution time on standard hardware:

| Step | Time | Notes |
|------|------|-------|
| Download | 1-3 min | Depends on connection speed |
| Extract | 10-20 sec | |
| Load Data | 5-10 sec | |
| Preprocess | 10-20 sec | |
| Feature Engineering | 30-60 sec | Most time-intensive |
| Normalize | 5-10 sec | |
| Save | 10-20 sec | |
| **Total** | **2-5 min** | Without download |

**Dataset Size:**
- Raw: ~20 MB (compressed)
- Processed: ~50 MB (with all features)

---

## Best Practices

1. **Always version your data**
   ```bash
   mkdir -p data/v1.0/
   python scripts/download_and_prepare_dataset.py --data-dir data/v1.0
   ```

2. **Use version control for preprocessing parameters**
   - Document failure threshold used
   - Document window size
   - Keep preprocessing scripts in git

3. **Validate before training**
   - Review data_quality_report.txt
   - Check label distribution
   - Verify feature ranges

4. **Keep raw data**
   - Never delete original files
   - Store in separate directory
   - Use for reprocessing

5. **Log everything**
   - Use `--verbose` for debugging
   - Check logs for warnings
   - Archive logs with model versions

---

## References

- **Dataset Source**: [NASA Prognostics Data Repository](https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/)
- **Paper**: Saxena, A., & Goebel, K. (2008). Turbofan Engine Degradation Simulation Data Set. NASA Ames Prognostics Data Repository.

---

**Last Updated**: 2025-01-02  
**Script Version**: 1.0  
**Contact**: DRDO Development Team
