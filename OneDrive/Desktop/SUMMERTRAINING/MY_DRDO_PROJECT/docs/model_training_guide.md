# Model Training Guide - Quick Start

## Overview

The `train_model_production.py` script provides a complete MLOps implementation for training Random Forest models with comprehensive evaluation and artifact management.

## Quick Usage

### 1. **Basic Training** (with default parameters)

```bash
python scripts/train_model_production.py \
  --data-dir ./data/processed \
  --model-dir ./models
```

### 2. **Training with Hyperparameter Tuning**

```bash
python scripts/train_model_production.py \
  --data-dir ./data/processed \
  --model-dir ./models \
  --tune-hyperparameters \
  --verbose
```

### 3. **Custom Configuration**

```bash
python scripts/train_model_production.py \
  --data-dir ./data/processed \
  --model-dir ./models \
  --n-estimators 200 \
  --max-depth 15 \
  --model-version v2 \
  --verbose
```

## Expected Output

```
================================================================================
EQUIPMENT FAILURE PREDICTION MODEL TRAINING
================================================================================

[STEP 1/6] Loading and validating data...
✓ Data loaded: Train=(20631, 58), Test=(10000, 58)
✓ Data validation passed

[STEP 2/6] Preparing data for training...
✓ Data prepared: Features=58, Train=20631, Test=10000

[STEP 3/6] Performing cross-validation...
  CV accuracy: 0.8810 ± 0.0080
  CV precision: 0.8523 ± 0.0125
  CV recall: 0.9095 ± 0.0103
  CV f1: 0.8800 ± 0.0095
  CV roc_auc: 0.9345 ± 0.0067

[STEP 4/6] Tuning hyperparameters...
✓ Grid search completed in 245.3 seconds
  Best parameters: {'class_weight': 'balanced', 'max_depth': 10, ...}
  Best CV F1 score: 0.8865

[STEP 5/6] Training final model...
✓ Model training completed in 12.45 seconds

[STEP 6/6] Evaluating model...
================================================================================
EVALUATION METRICS
================================================================================
Accuracy:  0.8810
Precision: 0.8523
Recall:    0.9095
F1-Score:  0.8800
ROC-AUC:   0.9345
================================================================================

Validating performance against thresholds...
  accuracy: 0.8810 >= 0.8500 [✓ PASS]
  precision: 0.8523 >= 0.8000 [✓ PASS]
  recall: 0.9095 >= 0.9000 [✓ PASS]
  f1_score: 0.8800 >= 0.8500 [✓ PASS]

Top 5 Most Important Features:
  1. sensor_2_rolling_mean: 0.1423
  2. sensor_3_rolling_std: 0.1187
  3. sensor_8_diff: 0.0956
  4. temp_vibration_interaction: 0.0834
  5. sensor_9_rolling_mean: 0.0723

✓ Confusion matrix saved: models/confusion_matrix_v1.png
✓ ROC curve saved: models/roc_curve_v1.png
✓ Feature importance plot saved: models/feature_importance_v1.png
✓ Model saved: models/failure_predictor_v1.pkl
✓ Feature names saved: models/feature_names_v1.json
✓ Model metadata saved: models/model_metadata_v1.json

================================================================================
✓ Training completed successfully!
✓ Model meets all performance thresholds
✓ Model artifacts saved to: models
================================================================================
```

## Output Files

After training, you'll find:

```
models/
├── failure_predictor_v1.pkl        # Trained model
├── feature_names_v1.json          # Feature list
├── model_metadata_v1.json         # Model metadata
├── training_report_v1.txt         # Detailed report
├── confusion_matrix_v1.png        # Confusion matrix plot
├── roc_curve_v1.png              # ROC curve plot
└── feature_importance_v1.png      # Feature importance plot

logs/
└── model_training_20250102_143045.log  # Training logs
```

## Key Features

✅ **Data Validation**: Checks for missing values, class imbalance  
✅ **Cross-Validation**: 5-fold stratified CV with multiple metrics  
✅ **Hyperparameter Tuning**: GridSearchCV with comprehensive param grid  
✅ **Comprehensive Metrics**: Accuracy, Precision, Recall, F1, ROC-AUC, MCC  
✅ **Visualizations**: Confusion matrix, ROC curve, feature importance  
✅ **Performance Validation**: Automatic threshold checking  
✅ **Artifact Management**: Versioned model saving  
✅ **Complete Logging**: Timestamped logs with all training details

## Integration with Existing Project

This script integrates perfectly with:

1. **Dataset preparation script** (`download_and_prepare_dataset.py`)  
   → Processes NASA turbofan data → Feeds into this training script

2. **ML Prediction Service** (`ml-prediction-service`)  
   → This script saves models → Service loads them for inference

Complete pipeline:
```
download_and_prepare_dataset.py → train_model_production.py → ml-prediction-service
```

🎯 **You now have a complete, production-ready ML training pipeline!**
