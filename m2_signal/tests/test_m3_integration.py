"""
test_m3_integration.py
Tests for m3_integration.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m3_integration import M2M3Bridge, scan, scan_all


def test_bridge_init():
    """Test bridge initialization in mock mode."""
    bridge = M2M3Bridge(m3_available=False, seed=42)
    assert bridge is not None
    assert bridge.m3_available == False
    print("✅ test_bridge_init passed")


def test_scan_single_region():
    """Test single region scan via bridge."""
    bridge = M2M3Bridge(m3_available=False, seed=42)
    obs = bridge.scan_region("R7")
    
    assert obs["region_id"] == "R7"
    assert "detected" in obs
    assert "confidence" in obs
    print("✅ test_scan_single_region passed")


def test_scan_multiple_regions():
    """Test multiple region scan via bridge."""
    bridge = M2M3Bridge(m3_available=False, seed=42)
    results = bridge.scan_multiple_regions(["R1", "R2", "R3"])
    
    assert len(results) == 3
    assert results[0]["region_id"] == "R1"
    assert results[1]["region_id"] == "R2"
    assert results[2]["region_id"] == "R3"
    print("✅ test_scan_multiple_regions passed")


def test_convenience_scan():
    """Test convenience scan function."""
    obs = scan("R7", seed=42)
    assert obs["region_id"] == "R7"
    print("✅ test_convenience_scan passed")


def test_convenience_scan_all():
    """Test convenience scan_all function."""
    results = scan_all(["R1", "R2", "R3"], seed=42)
    assert len(results) == 3
    print("✅ test_convenience_scan_all passed")


def test_signal_classification():
    """Test signal classification logic."""
    bridge = M2M3Bridge(m3_available=False, seed=42)
    
    # Based on actual _classify_signal logic:
    # strength > 0.7 and snr > 10  → "continuous"
    # strength > 0.4 and snr > 5   → "changing-strength"
    # bandwidth > 0.5              → "noisy"
    # else                         → "intermittent"
    
    assert bridge._classify_signal(0.8, 0.3, 12.0) == "continuous"
    assert bridge._classify_signal(0.5, 0.3, 7.0)  == "changing-strength"
    assert bridge._classify_signal(0.3, 0.7, 4.0)  == "noisy"
    assert bridge._classify_signal(0.2, 0.2, 3.0)  == "intermittent"
    print("✅ test_signal_classification passed")

def test_environment_status():
    """Test environment status report."""
    bridge = M2M3Bridge(m3_available=False, seed=42)
    status = bridge.get_environment_status()
    
    assert "m3_available" in status
    assert "m2_ready" in status
    assert status["m2_ready"] == True
    print("✅ test_environment_status passed")


if __name__ == "__main__":
    test_bridge_init()
    test_scan_single_region()
    test_scan_multiple_regions()
    test_convenience_scan()
    test_convenience_scan_all()
    test_signal_classification()
    test_environment_status()
    print("\n🎉 All m3_integration tests passed!")