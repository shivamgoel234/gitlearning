"""
Tests for ML model loading and prediction logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


def test_ml_model_initialization():
    """Test ML model initialization."""
    from app.ml_model import MLModel
    
    model = MLModel()
    
    assert model.model is None
    assert model.scaler is None
    assert model.feature_names == []
    assert model.is_loaded == False


@pytest.mark.skip("Requires actual model files")
def test_ml_model_load():
    """Test ML model loading from files."""
    from app.ml_model import MLModel
    
    model = MLModel()
    model.load_model()
    
    assert model.is_loaded == True
    assert model.model is not None
    assert model.scaler is not None
    assert len(model.feature_names) > 0


def test_extract_features():
    """Test feature extraction from sensor data."""
    from app.ml_model import MLModel
    
    model = MLModel()
    model.feature_names = ['temperature', 'vibration', 'pressure', 'humidity', 'voltage']
    
    sensor_data = {
        'temperature': 85.5,
        'vibration': 0.45,
        'pressure': 3.2,
        'humidity': 65.0,
        'voltage': 220.0
    }
    
    features = model._extract_features(sensor_data)
    
    assert features.shape == (1, 5)
    assert features[0][0] == 85.5
    assert features[0][1] == 0.45


def test_calculate_severity():
    """Test severity calculation."""
    from app.ml_model import MLModel
    
    model = MLModel()
    
    # Test CRITICAL
    severity, days = model._calculate_severity(0.85)
    assert severity == "CRITICAL"
    assert days == 7
    
    # Test HIGH
    severity, days = model._calculate_severity(0.65)
    assert severity == "HIGH"
    assert days == 15
    
    # Test MEDIUM
    severity, days = model._calculate_severity(0.45)
    assert severity == "MEDIUM"
    assert days == 30
    
    # Test LOW
    severity, days = model._calculate_severity(0.25)
    assert severity == "LOW"
    assert days == 60


def test_calculate_confidence():
    """Test confidence calculation."""
    from app.ml_model import MLModel
    
    model = MLModel()
    
    # High confidence (near 0 or 1)
    assert model._calculate_confidence(0.95) == "high"
    assert model._calculate_confidence(0.05) == "high"
    
    # Medium confidence
    assert model._calculate_confidence(0.70) == "medium"
    assert model._calculate_confidence(0.30) == "medium"
    
    # Low confidence (near 0.5)
    assert model._calculate_confidence(0.52) == "low"
    assert model._calculate_confidence(0.48) == "low"
