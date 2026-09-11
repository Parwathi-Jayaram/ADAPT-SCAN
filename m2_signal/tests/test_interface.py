"""
test_interface.py
Tests for m2_interface.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m2_interface import M2Interface, generate_observation, validate_scanner_result


def test_generate_observation():
    """Test basic observation generation."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.generate_observation({"region_id": "R7"})
    
    assert obs["region_id"] == "R7"
    assert "detected" in obs
    assert "strength" in obs
    assert "confidence" in obs
    assert "confidence_level" in obs
    assert "features" in obs
    assert len(obs["features"]) == 8
    print("✅ test_generate_observation passed")


def test_output_format():
    """Test output has all required fields."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.generate_observation({"region_id": "R7"})
    
    required_fields = [
        "region_id", "detected", "strength", "bandwidth",
        "snr", "confidence", "confidence_level",
        "features", "feature_meaning", "timestamp"
    ]
    
    for field in required_fields:
        assert field in obs, f"Missing field: {field}"
    print("✅ test_output_format passed")


def test_timestamp_is_float():
    """Test timestamp is always float."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.generate_observation({"region_id": "R7"})
    
    assert isinstance(obs["timestamp"], float)
    print("✅ test_timestamp_is_float passed")


def test_features_in_range():
    """Test all features are in 0.0–1.0 range."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.generate_observation({"region_id": "R7"})
    
    for i, f in enumerate(obs["features"]):
        assert 0.0 <= f <= 1.0, f"Feature {i} out of range: {f}"
    print("✅ test_features_in_range passed")


def test_validation_missing_region_id():
    """Test validation catches missing region_id."""
    try:
        validate_scanner_result({})
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ test_validation_missing_region_id passed")


def test_validation_wrong_type():
    """Test validation catches wrong type."""
    try:
        validate_scanner_result({"region_id": 123})
        assert False, "Should have raised TypeError"
    except TypeError:
        print("✅ test_validation_wrong_type passed")


def test_confidence_level():
    """Test confidence_level is valid string."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.generate_observation({"region_id": "R7"})
    
    valid_levels = ["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW"]
    assert obs["confidence_level"] in valid_levels
    print("✅ test_confidence_level passed")


def test_no_signal_handling():
    """Test no-signal case."""
    m2 = M2Interface(noise_level="medium", seed=42)
    obs = m2.handle_no_signal("R99")
    
    assert obs["region_id"] == "R99"
    assert obs["detected"] == False
    assert obs["strength"] == 0.0
    assert obs["confidence"] == 0.0
    print("✅ test_no_signal_handling passed")


def test_reproducibility():
    """Test reproducibility with same seed."""
    m2a = M2Interface(noise_level="medium", seed=42)
    m2b = M2Interface(noise_level="medium", seed=42)
    
    obs1 = m2a.generate_observation({"region_id": "R7"})
    obs2 = m2b.generate_observation({"region_id": "R7"})
    
    assert obs1["detected"] == obs2["detected"]
    assert obs1["confidence"] == obs2["confidence"]
    print("✅ test_reproducibility passed")


if __name__ == "__main__":
    test_generate_observation()
    test_output_format()
    test_timestamp_is_float()
    test_features_in_range()
    test_validation_missing_region_id()
    test_validation_wrong_type()
    test_confidence_level()
    test_no_signal_handling()
    test_reproducibility()
    print("\n🎉 All interface tests passed!")