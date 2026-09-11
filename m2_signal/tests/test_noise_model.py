"""
test_noise_model.py
Tests for noise_model.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noise_model import get_noise_config, apply_noise


def test_low_noise_config():
    """Test low noise configuration."""
    config = get_noise_config("low")
    assert config["noise_strength"] == 0.03
    assert config["missing_probability"] == 0.0
    print("✅ test_low_noise_config passed")


def test_medium_noise_config():
    """Test medium noise configuration."""
    config = get_noise_config("medium")
    assert config["noise_strength"] == 0.08
    assert config["missing_probability"] == 0.03
    print("✅ test_medium_noise_config passed")


def test_high_noise_config():
    """Test high noise configuration."""
    config = get_noise_config("high")
    assert config["noise_strength"] == 0.15
    assert config["missing_probability"] == 0.08
    print("✅ test_high_noise_config passed")
    
def test_invalid_noise_level():
    """Test that invalid level raises error."""
    try:
        get_noise_config("extreme")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ test_invalid_noise_level passed")


def test_apply_noise():
    """Test noise application."""
    noisy = apply_noise(0.8, 0.15, seed=42)
    assert 0.0 <= noisy <= 1.0
    print("✅ test_apply_noise passed")


def test_noise_reproducibility():
    """Test that same seed produces same noisy value."""
    noisy1 = apply_noise(0.8, 0.15, seed=42)
    noisy2 = apply_noise(0.8, 0.15, seed=42)
    assert noisy1 == noisy2
    print("✅ test_noise_reproducibility passed")


def test_noise_clamping():
    """Test that noisy value stays within [0, 1]."""
    noisy = apply_noise(0.0, 0.3, seed=42)
    assert 0.0 <= noisy <= 1.0
    noisy = apply_noise(1.0, 0.3, seed=42)
    assert 0.0 <= noisy <= 1.0
    print("✅ test_noise_clamping passed")


if __name__ == "__main__":
    test_low_noise_config()
    test_medium_noise_config()
    test_high_noise_config()
    test_invalid_noise_level()
    test_apply_noise()
    test_noise_reproducibility()
    test_noise_clamping()
    print("\n🎉 All noise_model tests passed!")