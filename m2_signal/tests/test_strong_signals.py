# test_strong_signals.py - Quick test for stronger signals
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m2_interface import M2Interface

print("=" * 60)
print("TESTING WITH STRONGER SIGNALS")
print("=" * 60)

m2 = M2Interface(noise_level="medium", seed=42)

# Test with default (now stronger)
print("\n1. Testing default signal (stronger):")
obs = m2.generate_observation({
    "region_id": "R7",
    "signal_type": "continuous"
})
print(f"   Detected: {obs['detected']}")
print(f"   Strength: {obs['strength']:.3f}")
print(f"   Confidence: {obs['confidence']:.3f}")

# Test with forced strong signal
print("\n2. Testing forced strong signal:")
obs = m2.generate_observation({
    "region_id": "R7",
    "signal_type": "continuous",
    "force_strong": True
})
print(f"   Detected: {obs['detected']}")
print(f"   Strength: {obs['strength']:.3f}")
print(f"   Confidence: {obs['confidence']:.3f}")

# Test multiple regions
print("\n3. Testing multiple regions with stronger signals:")
regions = ["R1", "R2", "R3", "R4", "R5"]
for region in regions:
    obs = m2.generate_observation({
        "region_id": region,
        "force_strong": True  # Force strong for testing
    })
    print(f"   {region}: detected={obs['detected']}, "
          f"strength={obs['strength']:.3f}, "
          f"confidence={obs['confidence']:.3f}")