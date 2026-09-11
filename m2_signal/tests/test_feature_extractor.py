"""
test_feature_extractor.py
Tests for feature_extractor.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_generator import generate_signal
from observation import ObservationModel
from feature_extractor import FeatureExtractor, extract_features


def test_basic_feature_extraction():
    """Test basic feature extraction."""
    gt = generate_signal("R7", "continuous", seed=42)
    model = ObservationModel("medium", seed=42)
    obs = model.observe(gt)
    
    features = extract_features(obs)
    assert features.region_id == "R7"
    assert 0.0 <= features.detection_confidence <= 1.0
    assert 0.0 <= features.uncertainty <= 1.0
    assert 0.0 <= features.reliability <= 1.0
    print("✅ test_basic_feature_extraction passed")


def test_feature_ranges():
    """Test that all features are in 0.0–1.0 range."""
    gt = generate_signal("R7", "continuous", seed=42)
    model = ObservationModel("medium", seed=42)
    obs = model.observe(gt)
    
    features = extract_features(obs)
    
    # Check all scalar features
    assert 0.0 <= features.detection_confidence <= 1.0
    assert 0.0 <= features.strength_estimate <= 1.0
    assert 0.0 <= features.bandwidth_estimate <= 1.0
    assert 0.0 <= features.uncertainty <= 1.0
    assert 0.0 <= features.reliability <= 1.0
    print("✅ test_feature_ranges passed")


def test_low_uncertainty_when_not_detected():
    """Test that uncertainty is low when nothing detected."""
    gt = generate_signal("R7", "continuous", seed=42)
    model = ObservationModel("high", seed=42)
    obs = model.observe(gt)
    
    features = extract_features(obs)
    if not obs.detected:
        assert features.uncertainty <= 0.2, f"Expected low uncertainty, got {features.uncertainty}"
    print("✅ test_low_uncertainty_when_not_detected passed")


def test_temporal_features():
    """Test temporal feature extraction."""
    extractor = FeatureExtractor(history_length=10)
    model = ObservationModel("medium", seed=42)
    
    for i in range(5):
        gt = generate_signal("R7", "continuous", seed=42 + i)
        obs = model.observe(gt)
        features = extractor.extract(obs)
    
    assert features.temporal_features["trend"] in ["increasing", "decreasing", "stable", "insufficient_data"]
    print("✅ test_temporal_features passed")


def test_region_summary():
    """Test region summary."""
    extractor = FeatureExtractor()
    model = ObservationModel("medium", seed=42)
    
    for i in range(3):
        gt = generate_signal("R7", "continuous", seed=42 + i)
        obs = model.observe(gt)
        extractor.extract(obs)
    
    summary = extractor.get_region_summary("R7")
    assert summary["region_id"] == "R7"
    assert 0.0 <= summary["confidence"] <= 1.0
    print("✅ test_region_summary passed")


if __name__ == "__main__":
    test_basic_feature_extraction()
    test_feature_ranges()
    test_low_uncertainty_when_not_detected()
    test_temporal_features()
    test_region_summary()
    print("\n🎉 All feature_extractor tests passed!")