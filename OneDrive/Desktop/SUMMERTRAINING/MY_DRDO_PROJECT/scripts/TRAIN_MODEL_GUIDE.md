# Model Training Guide - train_model.py

Complete guide for training Random Forest models for equipment failure prediction.

## 🎯 Overview

The `train_model.py` script provides a production-ready ML training pipeline with:

✅ **Data Validation** - Checks for missing values and required columns  
✅ **Feature Scaling** - StandardScaler for consistent predictions  
✅ **Stratified Split** - 80-20 train-test with class balance  
✅ **Cross-Validation** - 5-fold stratified CV for robust evaluation  
✅ **Hyperparameter Tuning** - Optional GridSearchCV  
✅ **Comprehensive Metrics** - Accuracy, Precision, Recall, F1, ROC-AUC  
✅ **Artifact Management** - Saves model, scaler, metadata, and reports  
✅ **Logging** - Detailed logs for debugging and auditing  

## 📋 Requirements

### Input Data Format

CSV file with the following columns:

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| `temperature` | float | -50 to 200 | Temperature in Celsius |
| `vibration` | float | 0 to 2.0 | Vibration level in mm/s |
| `pressure` | float | 0 to 10.0 | Pressure in bar |
| `humidity` | float | 0 to 100 | Humidity percentage |
| `voltage` | float | 0 to 500 | Voltage in volts |
| `failure_label` | int | 0 or 1 | 1 = failure within 30 days, 0 = normal |

### Python Dependencies

```bash
pip install numpy pandas scikit-learn joblib
```

## 🚀 Quick Start

### Basic Training (Default Parameters)

```bash
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --output-dir ./models
```

**Output**: Model artifacts in `./models/` directory

### Training with Hyperparameter Tuning

```bash
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --output-dir ./models \
  --tune-hyperparameters
```

**Note**: Hyperparameter tuning takes significantly longer (~10-30 minutes)

### Custom Configuration

```bash
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --output-dir ./services/ml-prediction/models \
  --test-size 0.2 \
  --cv-folds 5 \
  --random-seed 42 \
  --model-version v2
```

## 📊 Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--data-path` | str | **Required** | Path to training data CSV |
| `--output-dir` | str | `./services/ml-prediction/models` | Output directory for artifacts |
| `--test-size` | float | `0.2` | Test set proportion (0-1) |
| `--cv-folds` | int | `5` | Number of cross-validation folds |
| `--random-seed` | int | `42` | Random seed for reproducibility |
| `--tune-hyperparameters` | flag | `False` | Enable hyperparameter tuning |
| `--model-version` | str | `v1` | Model version identifier |

## 📁 Output Artifacts

After training, the following files are saved to `--output-dir`:

```
models/
├── failure_predictor_v1.pkl        # Trained Random Forest model
├── scaler_v1.pkl                   # Fitted StandardScaler
├── feature_names_v1.json           # Feature list (in order)
├── model_metadata_v1.json          # Model metadata and metrics
└── training_report_v1.txt          # Detailed training report
```

### Model Metadata JSON Structure

```json
{
  "model_type": "RandomForestClassifier",
  "version": "v1",
  "trained_date": "2025-11-02T10:30:00Z",
  "accuracy": 0.88,
  "precision": 0.85,
  "recall": 0.91,
  "f1_score": 0.88,
  "roc_auc": 0.93,
  "training_samples": 16505,
  "test_samples": 4126,
  "features": ["temperature", "vibration", "pressure", "humidity", "voltage"],
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "class_weight": "balanced"
  },
  "random_seed": 42,
  "cross_validation": {
    "cv_accuracy_mean": 0.8810,
    "cv_accuracy_std": 0.0080,
    "cv_precision_mean": 0.8523,
    "cv_precision_std": 0.0125,
    "cv_recall_mean": 0.9095,
    "cv_recall_std": 0.0103,
    "cv_f1_mean": 0.8800,
    "cv_f1_std": 0.0095,
    "cv_roc_auc_mean": 0.9345,
    "cv_roc_auc_std": 0.0067
  },
  "confusion_matrix": {
    "true_negatives": 2850,
    "false_positives": 185,
    "false_negatives": 95,
    "true_positives": 996
  },
  "feature_importance": {
    "temperature": 0.2543,
    "vibration": 0.2187,
    "pressure": 0.1956,
    "voltage": 0.1734,
    "humidity": 0.1580
  }
}
```

## 📈 Expected Output

### Console Output

```
================================================================================
EQUIPMENT FAILURE PREDICTION MODEL TRAINING
================================================================================
Data path: ./data/processed/train_data.csv
Output directory: ./models
Test size: 0.2
CV folds: 5
Random seed: 42
Hyperparameter tuning: False
================================================================================

2025-11-02 10:30:00 - INFO - ModelTrainer initialized
2025-11-02 10:30:01 - INFO - Loading data from ./data/processed/train_data.csv
2025-11-02 10:30:02 - INFO - Data loaded successfully: 20631 rows, 6 columns
2025-11-02 10:30:02 - INFO - Data validation passed
2025-11-02 10:30:02 - INFO - Preparing data for training
2025-11-02 10:30:02 - INFO - Class distribution: {0: 15473, 1: 5158}
2025-11-02 10:30:02 - INFO - Class imbalance ratio (normal/failure): 3.00
2025-11-02 10:30:02 - INFO - Train set size: 16505 samples
2025-11-02 10:30:02 - INFO - Test set size: 4126 samples
2025-11-02 10:30:02 - INFO - Scaling features using StandardScaler
2025-11-02 10:30:02 - INFO - Data preparation completed
2025-11-02 10:30:02 - INFO - Training Random Forest classifier
2025-11-02 10:30:15 - INFO - Model training completed
2025-11-02 10:30:15 - INFO - Performing 5-fold cross-validation

Cross-validation results:
  Accuracy:  0.8810 ± 0.0080
  Precision: 0.8523 ± 0.0125
  Recall:    0.9095 ± 0.0103
  F1:        0.8800 ± 0.0095
  ROC-AUC:   0.9345 ± 0.0067

================================================================================
TEST SET EVALUATION METRICS
================================================================================
Accuracy:  0.8810
Precision: 0.8523
Recall:    0.9095
F1-Score:  0.8800
ROC-AUC:   0.9345
--------------------------------------------------------------------------------
Confusion Matrix:
  TN:  2850  |  FP:   185
  FN:    95  |  TP:   996
--------------------------------------------------------------------------------
Feature Importance:
  temperature    : 0.2543
  vibration      : 0.2187
  pressure       : 0.1956
  voltage        : 0.1734
  humidity       : 0.1580
================================================================================

✓ Model meets all performance thresholds

✓ Model saved: models/failure_predictor_v1.pkl
✓ Scaler saved: models/scaler_v1.pkl
✓ Feature names saved: models/feature_names_v1.json
✓ Metadata saved: models/model_metadata_v1.json
✓ Training report saved: models/training_report_v1.txt

================================================================================
✓ TRAINING COMPLETED SUCCESSFULLY
================================================================================
Model artifacts saved to: ./models
================================================================================
```

## 🎯 Performance Thresholds

The script validates against minimum performance requirements:

| Metric | Minimum | Importance |
|--------|---------|------------|
| **Accuracy** | 85% | Overall correctness |
| **Precision** | 80% | Avoid false alarms |
| **Recall** | 90% | **CRITICAL** - Catch failures |

**Why high recall?** Missing a real failure (false negative) is more costly than a false alarm (false positive) in maintenance scenarios.

## 🔧 Hyperparameter Tuning

When using `--tune-hyperparameters`, the script searches over:

```python
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'class_weight': ['balanced', 'balanced_subsample']
}
```

**Total combinations**: 3 × 4 × 3 × 3 × 2 = 216 models trained

**Estimated time**: 15-45 minutes (depending on data size and CPU)

## 🐛 Troubleshooting

### Error: FileNotFoundError

```
FileNotFoundError: Data file not found: ./data/processed/train_data.csv
```

**Solution**: Check that data path is correct and file exists

```bash
# List files
ls ./data/processed/

# Use absolute path
python scripts/train_model.py --data-path "C:/full/path/to/data.csv"
```

### Error: Missing required features

```
ValueError: Missing required features: ['humidity', 'voltage']
```

**Solution**: Ensure CSV has all required columns:
- temperature
- vibration
- pressure
- humidity
- voltage
- failure_label

### Error: Target variable must have at least 2 classes

```
ValueError: Target variable must have at least 2 classes
```

**Solution**: Check that `failure_label` column has both 0 and 1 values

```python
import pandas as pd
df = pd.read_csv('data.csv')
print(df['failure_label'].value_counts())
```

### Warning: Model does not meet minimum performance thresholds

```
WARNING: Recall 0.8523 < 0.9000
```

**Solution**: Try:
1. Collect more training data
2. Engineer better features
3. Use hyperparameter tuning (`--tune-hyperparameters`)
4. Adjust class weights in code

## 📚 Using Trained Model in Production

### Load Model for Inference

```python
import joblib
import json
import numpy as np

# Load model and scaler
model = joblib.load('models/failure_predictor_v1.pkl')
scaler = joblib.load('models/scaler_v1.pkl')

# Load feature names
with open('models/feature_names_v1.json', 'r') as f:
    feature_names = json.load(f)

# Prepare input data (in correct order!)
sensor_data = {
    'temperature': 85.5,
    'vibration': 0.45,
    'pressure': 3.2,
    'humidity': 65.0,
    'voltage': 220.0
}

# Extract features in correct order
X = np.array([[sensor_data[f] for f in feature_names]])

# Scale features
X_scaled = scaler.transform(X)

# Predict
prediction = model.predict(X_scaled)[0]
probability = model.predict_proba(X_scaled)[0, 1]

print(f"Failure prediction: {prediction}")
print(f"Failure probability: {probability:.3f}")

# Interpret result
if prediction == 1:
    print("⚠️ Equipment likely to fail within 30 days")
else:
    print("✓ Equipment operating normally")
```

## 🎓 Advanced Usage

### Training Multiple Models

```bash
# Train baseline model
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --model-version v1_baseline

# Train tuned model
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --tune-hyperparameters \
  --model-version v2_tuned

# Train with different test split
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --test-size 0.3 \
  --model-version v3_larger_test
```

### Batch Training Script

Create `train_all_models.sh`:

```bash
#!/bin/bash

echo "Training multiple model variants..."

# Baseline
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --model-version v1_baseline

# With tuning
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --tune-hyperparameters \
  --model-version v2_tuned

# Different random seed
python scripts/train_model.py \
  --data-path ./data/processed/train_data.csv \
  --random-seed 123 \
  --model-version v3_seed123

echo "All models trained!"
```

## 📊 Model Comparison

After training multiple models, compare them:

```python
import json
import pandas as pd
from pathlib import Path

def compare_models(model_dir='./models'):
    """Compare all trained models."""
    results = []
    
    for metadata_file in Path(model_dir).glob('model_metadata_*.json'):
        with open(metadata_file, 'r') as f:
            meta = json.load(f)
            results.append({
                'version': meta['version'],
                'accuracy': meta['accuracy'],
                'precision': meta['precision'],
                'recall': meta['recall'],
                'f1_score': meta['f1_score'],
                'roc_auc': meta['roc_auc']
            })
    
    df = pd.DataFrame(results)
    print(df.sort_values('f1_score', ascending=False))
    
    return df

# Usage
df = compare_models()
```

## 🔗 Integration with Services

### ML Prediction Service

The trained model integrates with `services/ml-prediction/` service:

```python
# services/ml-prediction/app/model_loader.py
import joblib
from pathlib import Path

class ModelLoader:
    def __init__(self, model_dir='./models'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_names = None
        
    def load_latest(self, version='v1'):
        """Load latest model artifacts."""
        self.model = joblib.load(
            self.model_dir / f'failure_predictor_{version}.pkl'
        )
        self.scaler = joblib.load(
            self.model_dir / f'scaler_{version}.pkl'
        )
        with open(self.model_dir / f'feature_names_{version}.json') as f:
            self.feature_names = json.load(f)
        
        return self
```

---

## 📞 Support

For issues or questions:
1. Check logs in `logs/model_training.log`
2. Review training report in `models/training_report_v1.txt`
3. Verify data format matches requirements
4. Ensure all dependencies are installed

**Happy Training! 🚀**
