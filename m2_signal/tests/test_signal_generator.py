"""
test_signal_generator.py
Tests for signal_generator.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_generator import generate_signal


def test_continuous_signal():
    """Test continuous signal generation."""
    sig = generate_signal("R7", "continuous", seed=42)
    assert sig["region_id"] == "R7"
    assert sig["signal_type"] == "continuous"
    assert 0.0 <= sig["strength"] <= 1.0
    assert 0.0 <= sig["bandwidth"] <= 1.0
    assert sig["activity"] == 1.0
    print("✅ test_continuous_signal passed")


def test_intermittent_signal():
    """Test intermittent signal generation."""
    sig = generate_signal("R3", "intermittent", seed=42)
    assert sig["signal_type"] == "intermittent"
    assert 0.0 <= sig["activity"] <= 1.0
    print("✅ test_intermittent_signal passed")


def test_appearing_signal():
    """Test appearing signal generation."""
    sig = generate_signal("R5", "appearing", seed=42)
    assert sig["signal_type"] == "appearing"
    assert "start_time" in sig
    print("✅ test_appearing_signal passed")


def test_disappearing_signal():
    """Test disappearing signal generation."""
    sig = generate_signal("R9", "disappearing", seed=42)
    assert sig["signal_type"] == "disappearing"
    assert "end_time" in sig
    print("✅ test_disappearing_signal passed")


def test_changing_strength_signal():
    """Test changing-strength signal generation."""
    sig = generate_signal("R11", "changing-strength", seed=42)
    assert sig["signal_type"] == "changing-strength"
    assert "strength_change" in sig
    print("✅ test_changing_strength_signal passed")


def test_reproducibility():
    """Test that same seed produces same signal."""
    sig1 = generate_signal("R7", "continuous", seed=42)
    sig2 = generate_signal("R7", "continuous", seed=42)
    assert sig1["strength"] == sig2["strength"]
    assert sig1["bandwidth"] == sig2["bandwidth"]
    print("✅ test_reproducibility passed")


def test_invalid_signal_type():
    """Test that invalid signal type raises error."""
    try:
        generate_signal("R7", "invalid_type", seed=42)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ test_invalid_signal_type passed")


if __name__ == "__main__":
    test_continuous_signal()
    test_intermittent_signal()
    test_appearing_signal()
    test_disappearing_signal()
    test_changing_strength_signal()
    test_reproducibility()
    test_invalid_signal_type()
    print("\n🎉 All signal_generator tests passed!")