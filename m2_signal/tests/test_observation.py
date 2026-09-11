"""
test_observation.py
Tests for observation.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_generator import generate_signal
from observation import ObservationModel, create_observation


def test_basic_observation():
    """Test basic observation creation."""
    gt = generate_signal("R7", "continuous", seed=42)
    obs = create_observation(gt, "medium", seed=42)
    
    assert obs.region_id == "R7"
    assert isinstance(obs.detected, bool)
    assert 0.0 <= obs.strength <= 1.0
    assert 0.0 <= obs.confidence <= 1.0
    print("✅ test_basic_observation passed")


def test_observation_different_noise():
    """Test observation with different noise levels."""
    gt = generate_signal("R7", "continuous", seed=42)
    
    for level in ["low", "medium", "high"]:
        obs = create_observation(gt, level, seed=42)
        assert obs.region_id == "R7"
        assert 0.0 <= obs.confidence <= 1.0
    print("✅ test_observation_different_noise passed")


def test_observation_reproducibility():
    """Test observation reproducibility."""
    gt = generate_signal("R7", "continuous", seed=42)
    obs1 = create_observation(gt, "medium", seed=42)
    obs2 = create_observation(gt, "medium", seed=42)
    assert obs1.strength == obs2.strength
    print("✅ test_observation_reproducibility passed")


def test_observation_batch():
    """Test batch observation."""
    gts = [
        generate_signal("R1", "continuous", seed=1),
        generate_signal("R2", "intermittent", seed=2),
        generate_signal("R3", "appearing", seed=3),
    ]
    model = ObservationModel("medium", seed=42)
    obs_list = model.batch_observe(gts)
    
    assert len(obs_list) == 3
    assert obs_list[0].region_id == "R1"
    assert obs_list[1].region_id == "R2"
    assert obs_list[2].region_id == "R3"
    print("✅ test_observation_batch passed")


def test_no_detection_zeroes_strength():
    """Test that when detected=False, strength is zeroed."""
    gt = generate_signal("R7", "continuous", seed=42)
    obs = create_observation(gt, "high", seed=42)
    
    if not obs.detected:
        assert obs.strength == 0.0
        assert obs.confidence <= 0.2
    print("✅ test_no_detection_zeroes_strength passed")


if __name__ == "__main__":
    test_basic_observation()
    test_observation_different_noise()
    test_observation_reproducibility()
    test_observation_batch()
    test_no_detection_zeroes_strength()
    print("\n🎉 All observation tests passed!")