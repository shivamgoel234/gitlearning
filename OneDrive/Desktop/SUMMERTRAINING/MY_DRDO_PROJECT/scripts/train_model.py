"""
Random Forest Model Training Script for Equipment Failure Prediction.

This script trains a Random Forest classifier to predict equipment failures
within 30 days based on sensor readings (temperature, vibration, pressure, etc.).

Usage:
    python scripts/train_model.py --data-path ./data/processed/turbofan_data.csv \\
                                   --output-dir ./services/ml-prediction/models \\
                                   --test-size 0.2 \\
                                   --cv-folds 5 \\
                                   --random-seed 42

Author: DRDO Summer Training Project
Date: 2025-11-02
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Any, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
    StratifiedKFold,
    GridSearchCV,
)
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/model_training.log')
    ]
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Random Forest model trainer for equipment failure prediction.
    
    This class handles the complete ML pipeline from data loading to model
    evaluation and artifact saving.
    """
    
    def __init__(
        self,
        random_seed: int = 42,
        test_size: float = 0.2,
        cv_folds: int = 5,
        tune_hyperparameters: bool = False
    ):
        """
        Initialize the model trainer.
        
        Args:
            random_seed: Random seed for reproducibility
            test_size: Proportion of data for testing (0-1)
            cv_folds: Number of cross-validation folds
            tune_hyperparameters: Whether to perform hyperparameter tuning
        """
        self.random_seed = random_seed
        self.test_size = test_size
        self.cv_folds = cv_folds
        self.tune_hyperparameters = tune_hyperparameters
        
        self.model: RandomForestClassifier | None = None
        self.scaler: StandardScaler | None = None
        self.feature_names: List[str] = []
        self.metadata: Dict[str, Any] = {}
        
        logger.info(f"ModelTrainer initialized with random_seed={random_seed}, "
                   f"test_size={test_size}, cv_folds={cv_folds}")
    
    def load_data(self, data_path: str) -> pd.DataFrame:
        """
        Load training data from CSV file.
        
        Args:
            data_path: Path to CSV file
            
        Returns:
            DataFrame with loaded data
            
        Raises:
            FileNotFoundError: If data file doesn't exist
            ValueError: If required columns are missing
        """
        logger.info(f"Loading data from {data_path}")
        
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        try:
            df = pd.read_csv(data_path)
            logger.info(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Validate required columns
            required_features = ['temperature', 'vibration', 'pressure', 'humidity', 'voltage']
            missing_features = [f for f in required_features if f not in df.columns]
            
            if missing_features:
                raise ValueError(f"Missing required features: {missing_features}")
            
            if 'failure_label' not in df.columns:
                raise ValueError("Missing target column: 'failure_label'")
            
            logger.info(f"Data validation passed")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def prepare_data(
        self,
        df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for training: handle missing values, scale features, split.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        logger.info("Preparing data for training")
        
        # Define feature columns
        feature_cols = ['temperature', 'vibration', 'pressure', 'humidity', 'voltage']
        self.feature_names = feature_cols
        
        # Extract features and target
        X = df[feature_cols].values
        y = df['failure_label'].values
        
        # Check for missing values
        missing_count = pd.DataFrame(X, columns=feature_cols).isnull().sum().sum()
        if missing_count > 0:
            logger.warning(f"Found {missing_count} missing values, filling with median")
            X = pd.DataFrame(X, columns=feature_cols).fillna(
                pd.DataFrame(X, columns=feature_cols).median()
            ).values
        
        # Check class distribution
        unique, counts = np.unique(y, return_counts=True)
        class_distribution = dict(zip(unique, counts))
        logger.info(f"Class distribution: {class_distribution}")
        
        if len(unique) < 2:
            raise ValueError("Target variable must have at least 2 classes")
        
        # Calculate class imbalance ratio
        if 0 in class_distribution and 1 in class_distribution:
            imbalance_ratio = class_distribution[0] / class_distribution[1]
            logger.info(f"Class imbalance ratio (normal/failure): {imbalance_ratio:.2f}")
        
        # Train-test split with stratification
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_seed,
            stratify=y
        )
        
        logger.info(f"Train set size: {X_train.shape[0]} samples")
        logger.info(f"Test set size: {X_test.shape[0]} samples")
        
        # Feature scaling
        logger.info("Scaling features using StandardScaler")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info("Data preparation completed")
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> RandomForestClassifier:
        """
        Train Random Forest classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            
        Returns:
            Trained RandomForestClassifier
        """
        logger.info("Training Random Forest classifier")
        
        if self.tune_hyperparameters:
            logger.info("Performing hyperparameter tuning with GridSearchCV")
            model = self._train_with_tuning(X_train, y_train)
        else:
            logger.info("Training with default hyperparameters")
            model = self._train_default(X_train, y_train)
        
        self.model = model
        logger.info("Model training completed")
        return model
    
    def _train_default(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> RandomForestClassifier:
        """Train model with default hyperparameters."""
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight='balanced',
            random_state=self.random_seed,
            n_jobs=-1,
            verbose=1
        )
        
        model.fit(X_train, y_train)
        return model
    
    def _train_with_tuning(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> RandomForestClassifier:
        """Train model with hyperparameter tuning."""
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'class_weight': ['balanced', 'balanced_subsample']
        }
        
        base_model = RandomForestClassifier(
            random_state=self.random_seed,
            n_jobs=-1
        )
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=self.cv_folds,
            scoring='f1',
            n_jobs=-1,
            verbose=2
        )
        
        logger.info("Starting GridSearchCV...")
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV F1 score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def cross_validate(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> Dict[str, float]:
        """
        Perform cross-validation.
        
        Args:
            X_train: Training features
            y_train: Training labels
            
        Returns:
            Dictionary with cross-validation metrics
        """
        logger.info(f"Performing {self.cv_folds}-fold cross-validation")
        
        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_seed)
        
        # Accuracy
        cv_accuracy = cross_val_score(
            self.model, X_train, y_train, cv=cv, scoring='accuracy', n_jobs=-1
        )
        
        # Precision
        cv_precision = cross_val_score(
            self.model, X_train, y_train, cv=cv, scoring='precision', n_jobs=-1
        )
        
        # Recall
        cv_recall = cross_val_score(
            self.model, X_train, y_train, cv=cv, scoring='recall', n_jobs=-1
        )
        
        # F1
        cv_f1 = cross_val_score(
            self.model, X_train, y_train, cv=cv, scoring='f1', n_jobs=-1
        )
        
        # ROC-AUC
        cv_roc_auc = cross_val_score(
            self.model, X_train, y_train, cv=cv, scoring='roc_auc', n_jobs=-1
        )
        
        cv_results = {
            'cv_accuracy_mean': cv_accuracy.mean(),
            'cv_accuracy_std': cv_accuracy.std(),
            'cv_precision_mean': cv_precision.mean(),
            'cv_precision_std': cv_precision.std(),
            'cv_recall_mean': cv_recall.mean(),
            'cv_recall_std': cv_recall.std(),
            'cv_f1_mean': cv_f1.mean(),
            'cv_f1_std': cv_f1.std(),
            'cv_roc_auc_mean': cv_roc_auc.mean(),
            'cv_roc_auc_std': cv_roc_auc.std(),
        }
        
        logger.info("Cross-validation results:")
        logger.info(f"  Accuracy:  {cv_results['cv_accuracy_mean']:.4f} ± {cv_results['cv_accuracy_std']:.4f}")
        logger.info(f"  Precision: {cv_results['cv_precision_mean']:.4f} ± {cv_results['cv_precision_std']:.4f}")
        logger.info(f"  Recall:    {cv_results['cv_recall_mean']:.4f} ± {cv_results['cv_recall_std']:.4f}")
        logger.info(f"  F1:        {cv_results['cv_f1_mean']:.4f} ± {cv_results['cv_f1_std']:.4f}")
        logger.info(f"  ROC-AUC:   {cv_results['cv_roc_auc_mean']:.4f} ± {cv_results['cv_roc_auc_std']:.4f}")
        
        return cv_results
    
    def evaluate_model(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating model on test set")
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        # Classification report
        class_report = classification_report(y_test, y_pred, output_dict=True)
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        
        evaluation_results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': {
                'true_negatives': int(tn),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp)
            },
            'classification_report': class_report,
            'feature_importance': feature_importance
        }
        
        # Log metrics
        logger.info("=" * 80)
        logger.info("TEST SET EVALUATION METRICS")
        logger.info("=" * 80)
        logger.info(f"Accuracy:  {accuracy:.4f}")
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall:    {recall:.4f}")
        logger.info(f"F1-Score:  {f1:.4f}")
        logger.info(f"ROC-AUC:   {roc_auc:.4f}")
        logger.info("-" * 80)
        logger.info("Confusion Matrix:")
        logger.info(f"  TN: {tn:5d}  |  FP: {fp:5d}")
        logger.info(f"  FN: {fn:5d}  |  TP: {tp:5d}")
        logger.info("-" * 80)
        logger.info("Feature Importance:")
        for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {feature:15s}: {importance:.4f}")
        logger.info("=" * 80)
        
        # Check minimum performance thresholds
        self._validate_performance(accuracy, precision, recall)
        
        return evaluation_results
    
    def _validate_performance(
        self,
        accuracy: float,
        precision: float,
        recall: float
    ) -> None:
        """Validate model meets minimum performance thresholds."""
        min_accuracy = 0.85
        min_precision = 0.80
        min_recall = 0.90
        
        logger.info("Validating performance against thresholds...")
        
        failures = []
        if accuracy < min_accuracy:
            failures.append(f"Accuracy {accuracy:.4f} < {min_accuracy}")
        if precision < min_precision:
            failures.append(f"Precision {precision:.4f} < {min_precision}")
        if recall < min_recall:
            failures.append(f"Recall {recall:.4f} < {min_recall}")
        
        if failures:
            logger.warning("Model does not meet minimum performance thresholds:")
            for failure in failures:
                logger.warning(f"  - {failure}")
        else:
            logger.info("✓ Model meets all performance thresholds")
    
    def save_artifacts(
        self,
        output_dir: str,
        cv_results: Dict[str, float],
        eval_results: Dict[str, Any],
        X_train: np.ndarray,
        X_test: np.ndarray,
        model_version: str = "v1"
    ) -> None:
        """
        Save model artifacts.
        
        Args:
            output_dir: Directory to save artifacts
            cv_results: Cross-validation results
            eval_results: Evaluation results
            X_train: Training features (for sample counts)
            X_test: Test features (for sample counts)
            model_version: Model version string
        """
        logger.info(f"Saving model artifacts to {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = output_path / f"failure_predictor_{model_version}.pkl"
        joblib.dump(self.model, model_file)
        logger.info(f"✓ Model saved: {model_file}")
        
        # Save scaler
        scaler_file = output_path / f"scaler_{model_version}.pkl"
        joblib.dump(self.scaler, scaler_file)
        logger.info(f"✓ Scaler saved: {scaler_file}")
        
        # Save feature names
        feature_names_file = output_path / f"feature_names_{model_version}.json"
        with open(feature_names_file, 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        logger.info(f"✓ Feature names saved: {feature_names_file}")
        
        # Save metadata
        metadata = {
            "model_type": "RandomForestClassifier",
            "version": model_version,
            "trained_date": datetime.utcnow().isoformat() + "Z",
            "accuracy": eval_results['accuracy'],
            "precision": eval_results['precision'],
            "recall": eval_results['recall'],
            "f1_score": eval_results['f1_score'],
            "roc_auc": eval_results['roc_auc'],
            "training_samples": int(X_train.shape[0]),
            "test_samples": int(X_test.shape[0]),
            "features": self.feature_names,
            "hyperparameters": {
                "n_estimators": self.model.n_estimators,
                "max_depth": self.model.max_depth,
                "min_samples_split": self.model.min_samples_split,
                "min_samples_leaf": self.model.min_samples_leaf,
                "class_weight": str(self.model.class_weight),
            },
            "random_seed": self.random_seed,
            "cross_validation": cv_results,
            "confusion_matrix": eval_results['confusion_matrix'],
            "feature_importance": eval_results['feature_importance']
        }
        
        metadata_file = output_path / f"model_metadata_{model_version}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Metadata saved: {metadata_file}")
        
        # Save training report
        report_file = output_path / f"training_report_{model_version}.txt"
        self._save_training_report(report_file, cv_results, eval_results, metadata)
        logger.info(f"✓ Training report saved: {report_file}")
        
        logger.info("All artifacts saved successfully")
    
    def _save_training_report(
        self,
        report_file: Path,
        cv_results: Dict[str, float],
        eval_results: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """Save detailed training report to text file."""
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("EQUIPMENT FAILURE PREDICTION MODEL - TRAINING REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Model Type: {metadata['model_type']}\n")
            f.write(f"Version: {metadata['version']}\n")
            f.write(f"Trained: {metadata['trained_date']}\n")
            f.write(f"Random Seed: {metadata['random_seed']}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("DATASET INFORMATION\n")
            f.write("-" * 80 + "\n")
            f.write(f"Training Samples: {metadata['training_samples']}\n")
            f.write(f"Test Samples: {metadata['test_samples']}\n")
            f.write(f"Features: {', '.join(metadata['features'])}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("HYPERPARAMETERS\n")
            f.write("-" * 80 + "\n")
            for param, value in metadata['hyperparameters'].items():
                f.write(f"{param}: {value}\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("CROSS-VALIDATION RESULTS (5-FOLD)\n")
            f.write("-" * 80 + "\n")
            f.write(f"Accuracy:  {cv_results['cv_accuracy_mean']:.4f} ± {cv_results['cv_accuracy_std']:.4f}\n")
            f.write(f"Precision: {cv_results['cv_precision_mean']:.4f} ± {cv_results['cv_precision_std']:.4f}\n")
            f.write(f"Recall:    {cv_results['cv_recall_mean']:.4f} ± {cv_results['cv_recall_std']:.4f}\n")
            f.write(f"F1-Score:  {cv_results['cv_f1_mean']:.4f} ± {cv_results['cv_f1_std']:.4f}\n")
            f.write(f"ROC-AUC:   {cv_results['cv_roc_auc_mean']:.4f} ± {cv_results['cv_roc_auc_std']:.4f}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("TEST SET EVALUATION\n")
            f.write("-" * 80 + "\n")
            f.write(f"Accuracy:  {eval_results['accuracy']:.4f}\n")
            f.write(f"Precision: {eval_results['precision']:.4f}\n")
            f.write(f"Recall:    {eval_results['recall']:.4f}\n")
            f.write(f"F1-Score:  {eval_results['f1_score']:.4f}\n")
            f.write(f"ROC-AUC:   {eval_results['roc_auc']:.4f}\n\n")
            
            cm = eval_results['confusion_matrix']
            f.write("Confusion Matrix:\n")
            f.write(f"  TN: {cm['true_negatives']:5d}  |  FP: {cm['false_positives']:5d}\n")
            f.write(f"  FN: {cm['false_negatives']:5d}  |  TP: {cm['true_positives']:5d}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("FEATURE IMPORTANCE\n")
            f.write("-" * 80 + "\n")
            for feature, importance in sorted(
                eval_results['feature_importance'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                f.write(f"{feature:15s}: {importance:.4f}\n")
            
            f.write("\n" + "=" * 80 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Random Forest model for equipment failure prediction"
    )
    
    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Path to training data CSV file'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./services/ml-prediction/models',
        help='Directory to save model artifacts'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proportion of data for testing (default: 0.2)'
    )
    
    parser.add_argument(
        '--cv-folds',
        type=int,
        default=5,
        help='Number of cross-validation folds (default: 5)'
    )
    
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--tune-hyperparameters',
        action='store_true',
        help='Perform hyperparameter tuning with GridSearchCV'
    )
    
    parser.add_argument(
        '--model-version',
        type=str,
        default='v1',
        help='Model version identifier (default: v1)'
    )
    
    return parser.parse_args()


def main():
    """Main training pipeline."""
    # Parse arguments
    args = parse_arguments()
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("EQUIPMENT FAILURE PREDICTION MODEL TRAINING")
    logger.info("=" * 80)
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Test size: {args.test_size}")
    logger.info(f"CV folds: {args.cv_folds}")
    logger.info(f"Random seed: {args.random_seed}")
    logger.info(f"Hyperparameter tuning: {args.tune_hyperparameters}")
    logger.info("=" * 80)
    
    try:
        # Initialize trainer
        trainer = ModelTrainer(
            random_seed=args.random_seed,
            test_size=args.test_size,
            cv_folds=args.cv_folds,
            tune_hyperparameters=args.tune_hyperparameters
        )
        
        # Load data
        df = trainer.load_data(args.data_path)
        
        # Prepare data
        X_train, X_test, y_train, y_test = trainer.prepare_data(df)
        
        # Train model
        model = trainer.train_model(X_train, y_train)
        
        # Cross-validate
        cv_results = trainer.cross_validate(X_train, y_train)
        
        # Evaluate on test set
        eval_results = trainer.evaluate_model(X_test, y_test)
        
        # Save artifacts
        trainer.save_artifacts(
            args.output_dir,
            cv_results,
            eval_results,
            X_train,
            X_test,
            model_version=args.model_version
        )
        
        logger.info("=" * 80)
        logger.info("✓ TRAINING COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Model artifacts saved to: {args.output_dir}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("✗ TRAINING FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
