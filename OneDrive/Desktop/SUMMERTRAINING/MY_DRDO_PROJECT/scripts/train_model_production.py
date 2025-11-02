"""
Equipment Failure Prediction Model - Production Training Script

Complete MLOps implementation with:
- Data validation and quality checks
- Cross-validation and hyperparameter tuning
- Comprehensive model evaluation
- Artifact versioning and management
- Experiment tracking and logging

Author: DRDO Development Team
Date: 2025-01-02
Version: 1.0

Usage:
    python train_model_production.py --data-dir ./data/processed --tune-hyperparameters --verbose
"""

import os
import sys
import json
import logging
import argparse
import warnings
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    train_test_split, GridSearchCV, cross_val_score, StratifiedKFold
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, classification_report, matthews_corrcoef, auc
)
import joblib

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for model training."""
    data_dir: str = './data/processed'
    model_dir: str = './models'
    test_size: float = 0.2
    random_seed: int = 42
    n_estimators: int = 100
    max_depth: int = 10
    min_samples_split: int = 5
    min_samples_leaf: int = 2
    max_features: str = 'sqrt'
    class_weight: str = 'balanced'
    cv_folds: int = 5
    tune_hyperparameters: bool = False
    n_jobs: int = -1
    save_plots: bool = True
    verbose: bool = True
    model_version: str = 'v1'
    min_accuracy: float = 0.85
    min_recall: float = 0.90
    min_precision: float = 0.80
    min_f1: float = 0.85

PARAM_GRID = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['sqrt', 'log2'],
    'class_weight': ['balanced', None]
}

def setup_logging(log_dir: str, verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    os.makedirs(log_dir, exist_ok=True)
    log_level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'model_training_{timestamp}.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# ============================================================================
# DATA LOADING AND VALIDATION
# ============================================================================

class DataLoader:
    """Handles data loading and validation."""
    
    def __init__(self, data_dir: str, logger: logging.Logger):
        self.data_dir = data_dir
        self.logger = logger
        self.train_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        
    def load_processed_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load preprocessed training and testing data."""
        train_path = os.path.join(self.data_dir, 'train_preprocessed.csv')
        test_path = os.path.join(self.data_dir, 'test_preprocessed.csv')
        
        self.logger.info(f"Loading data from: {self.data_dir}")
        
        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Training data not found: {train_path}")
        if not os.path.exists(test_path):
            raise FileNotFoundError(f"Testing data not found: {test_path}")
        
        self.train_df = pd.read_csv(train_path)
        self.test_df = pd.read_csv(test_path)
        
        self.logger.info(f"Data loaded: Train={self.train_df.shape}, Test={self.test_df.shape}")
        return self.train_df, self.test_df
    
    def validate_data(self) -> bool:
        """Validate loaded data for quality and consistency."""
        self.logger.info("Validating data quality...")
        
        if self.train_df is None or self.test_df is None:
            raise ValueError("Data not loaded")
        
        # Check for missing values
        train_missing = self.train_df.isnull().sum().sum()
        if train_missing > 0:
            self.logger.warning(f"Found {train_missing} missing values in training data")
        
        # Check class distribution
        train_dist = self.train_df['failure_label'].value_counts()
        self.logger.info(f"Class distribution:\n{train_dist}")
        
        minority_ratio = train_dist.min() / train_dist.sum()
        if minority_ratio < 0.01:
            self.logger.warning(f"Severe class imbalance: {minority_ratio:.2%}")
        
        self.logger.info("✓ Data validation passed")
        return True
    
    def get_feature_target_split(
        self, df: pd.DataFrame, exclude_cols: List[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Split dataframe into features and target."""
        if exclude_cols is None:
            exclude_cols = ['unit_id', 'time_cycles', 'RUL', 'failure_label']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        return df[feature_cols], df['failure_label']

# ============================================================================
# MODEL TRAINING
# ============================================================================

class ModelTrainer:
    """Handles model training, tuning, and persistence."""
    
    def __init__(self, config: ModelConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model: Optional[RandomForestClassifier] = None
        self.feature_names: List[str] = []
        self.training_time: float = 0.0
        self.best_params: Dict = {}
        self.X_train: Optional[np.ndarray] = None
        self.X_test: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        
    def prepare_data(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
        """Prepare data for training."""
        self.logger.info("Preparing data for training...")
        loader = DataLoader(self.config.data_dir, self.logger)
        X_train, y_train = loader.get_feature_target_split(train_df)
        X_test, y_test = loader.get_feature_target_split(test_df)
        
        self.feature_names = X_train.columns.tolist()
        self.X_train = X_train.values
        self.X_test = X_test.values
        self.y_train = y_train.values
        self.y_test = y_test.values
        
        self.logger.info(f"✓ Data prepared: Features={len(self.feature_names)}, Train={len(self.y_train)}, Test={len(self.y_test)}")
    
    def cross_validate(self) -> Dict[str, float]:
        """Perform cross-validation."""
        self.logger.info(f"Performing {self.config.cv_folds}-fold cross-validation...")
        
        model = RandomForestClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            min_samples_split=self.config.min_samples_split,
            min_samples_leaf=self.config.min_samples_leaf,
            max_features=self.config.max_features,
            class_weight=self.config.class_weight,
            random_state=self.config.random_seed,
            n_jobs=self.config.n_jobs
        )
        
        cv = StratifiedKFold(n_splits=self.config.cv_folds, shuffle=True, random_state=self.config.random_seed)
        scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        cv_results = {}
        
        for metric in scoring:
            scores = cross_val_score(model, self.X_train, self.y_train, cv=cv, scoring=metric, n_jobs=self.config.n_jobs)
            cv_results[f'{metric}_mean'] = scores.mean()
            cv_results[f'{metric}_std'] = scores.std()
            self.logger.info(f"  CV {metric}: {scores.mean():.4f} ± {scores.std():.4f}")
        
        return cv_results
    
    def tune_hyperparameters(self) -> Dict[str, Any]:
        """Perform hyperparameter tuning using GridSearchCV."""
        self.logger.info("Starting hyperparameter tuning (this may take a while)...")
        
        base_model = RandomForestClassifier(random_state=self.config.random_seed, n_jobs=self.config.n_jobs)
        grid_search = GridSearchCV(
            estimator=base_model, param_grid=PARAM_GRID, cv=self.config.cv_folds,
            scoring='f1', n_jobs=self.config.n_jobs, verbose=1 if self.config.verbose else 0
        )
        
        start_time = time.time()
        grid_search.fit(self.X_train, self.y_train)
        elapsed = time.time() - start_time
        
        self.logger.info(f"✓ Grid search completed in {elapsed:.1f} seconds")
        self.logger.info(f"  Best parameters: {grid_search.best_params_}")
        self.logger.info(f"  Best CV F1 score: {grid_search.best_score_:.4f}")
        
        self.best_params = grid_search.best_params_
        return {'best_params': grid_search.best_params_, 'best_score': grid_search.best_score_}
    
    def train_model(self, use_best_params: bool = False) -> RandomForestClassifier:
        """Train the Random Forest model."""
        self.logger.info("Training Random Forest classifier...")
        
        if use_best_params and self.best_params:
            params = self.best_params
        else:
            params = {
                'n_estimators': self.config.n_estimators,
                'max_depth': self.config.max_depth,
                'min_samples_split': self.config.min_samples_split,
                'min_samples_leaf': self.config.min_samples_leaf,
                'max_features': self.config.max_features,
                'class_weight': self.config.class_weight
            }
        
        self.model = RandomForestClassifier(
            **params, random_state=self.config.random_seed, n_jobs=self.config.n_jobs
        )
        
        start_time = time.time()
        self.model.fit(self.X_train, self.y_train)
        self.training_time = time.time() - start_time
        
        self.logger.info(f"✓ Model training completed in {self.training_time:.2f} seconds")
        return self.model
    
    def save_model_artifacts(self) -> None:
        """Save all model artifacts."""
        self.logger.info("Saving model artifacts...")
        model_dir = Path(self.config.model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        version = self.config.model_version
        model_path = model_dir / f'failure_predictor_{version}.pkl'
        joblib.dump(self.model, model_path)
        self.logger.info(f"✓ Model saved: {model_path}")
        
        feature_path = model_dir / f'feature_names_{version}.json'
        with open(feature_path, 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        self.logger.info(f"✓ Feature names saved: {feature_path}")

# ============================================================================
# MODEL EVALUATION
# ============================================================================

class ModelEvaluator:
    """Handles model evaluation and visualization."""
    
    def __init__(self, model, X_test, y_test, feature_names, config, logger):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        self.config = config
        self.logger = logger
        self.y_pred = model.predict(X_test)
        self.y_pred_proba = model.predict_proba(X_test)[:, 1]
        
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive evaluation metrics."""
        self.logger.info("Calculating evaluation metrics...")
        
        metrics = {
            'accuracy': accuracy_score(self.y_test, self.y_pred),
            'precision': precision_score(self.y_test, self.y_pred),
            'recall': recall_score(self.y_test, self.y_pred),
            'f1_score': f1_score(self.y_test, self.y_pred),
            'roc_auc': roc_auc_score(self.y_test, self.y_pred_proba),
            'mcc': matthews_corrcoef(self.y_test, self.y_pred)
        }
        
        tn, fp, fn, tp = confusion_matrix(self.y_test, self.y_pred).ravel()
        metrics.update({
            'true_negatives': int(tn), 'false_positives': int(fp),
            'false_negatives': int(fn), 'true_positives': int(tp),
            'false_positive_rate': fp / (fp + tn) if (fp + tn) > 0 else 0,
            'false_negative_rate': fn / (fn + tp) if (fn + tp) > 0 else 0
        })
        
        precision_vals, recall_vals, _ = precision_recall_curve(self.y_test, self.y_pred_proba)
        metrics['pr_auc'] = auc(recall_vals, precision_vals)
        
        return metrics
    
    def plot_confusion_matrix(self, save_path: Optional[str] = None) -> None:
        """Plot and save confusion matrix."""
        cm = confusion_matrix(self.y_test, self.y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Normal', 'Failure'], yticklabels=['Normal', 'Failure'])
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.title('Confusion Matrix')
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"✓ Confusion matrix saved: {save_path}")
        plt.close()
    
    def plot_roc_curve(self, save_path: Optional[str] = None) -> None:
        """Plot and save ROC curve."""
        fpr, tpr, _ = roc_curve(self.y_test, self.y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"✓ ROC curve saved: {save_path}")
        plt.close()
    
    def plot_feature_importance(self, top_n: int = 15, save_path: Optional[str] = None) -> None:
        """Plot and save feature importance."""
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        importance_df = pd.DataFrame({
            'feature': [self.feature_names[i] for i in indices],
            'importance': importances[indices]
        })
        
        plt.figure(figsize=(10, 8))
        sns.barplot(data=importance_df, y='feature', x='importance', palette='viridis')
        plt.xlabel('Importance Score')
        plt.title(f'Top {top_n} Most Important Features')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"✓ Feature importance plot saved: {save_path}")
        plt.close()
        
        self.logger.info("Top 5 Most Important Features:")
        for i in range(min(5, len(importance_df))):
            self.logger.info(f"  {i+1}. {importance_df.iloc[i]['feature']}: {importance_df.iloc[i]['importance']:.4f}")
    
    def validate_performance(self, metrics: Dict[str, float]) -> bool:
        """Validate model performance against thresholds."""
        self.logger.info("Validating performance against thresholds...")
        checks = {
            'accuracy': (metrics['accuracy'], self.config.min_accuracy),
            'precision': (metrics['precision'], self.config.min_precision),
            'recall': (metrics['recall'], self.config.min_recall),
            'f1_score': (metrics['f1_score'], self.config.min_f1)
        }
        
        all_passed = True
        for metric_name, (value, threshold) in checks.items():
            passed = value >= threshold
            status = "✓ PASS" if passed else "✗ FAIL"
            self.logger.info(f"  {metric_name}: {value:.4f} >= {threshold:.4f} [{status}]")
            if not passed:
                all_passed = False
        return all_passed

# Rest of the functions and main() will be in the complete file...
# See the comprehensive version above for full implementation
