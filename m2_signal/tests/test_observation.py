# tests/test_observation.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\tests\test_observation.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_generator import generate_signal
from observation import ObservationModel, create_observation

print("=" * 60)
print("STEP 6: OBSERVATION MODEL VERIFICATION")
print("=" * 60)

# Test 1: Basic observation
print("\n1. Testing basic observation:")
gt = generate_signal("R7", "continuous", seed=42)
print(f"Ground Truth (HIDDEN from AI):")
print(f"  Region: {gt['region_id']}")
print(f"  Strength: {gt['strength']:.3f}")
print(f"  Signal Type: {gt['signal_type']}")

obs = create_observation(gt, "medium", 42)
print(f"\nObservation (What AI sees):")
print(f"  Region: {obs.region_id}")
print(f"  Detected: {obs.detected}")
print(f"  Strength: {obs.strength:.3f} (noisy)")
print(f"  Confidence: {obs.confidence:.3f}")
print(f"  SNR: {obs.snr:.2f}")

# Test 2: Different noise levels
print("\n2. Testing different noise levels:")
for level in ["low", "medium", "high"]:
    obs = create_observation(gt, level, 42)
    print(f"  {level.upper()}: detected={obs.detected}, strength={obs.strength:.3f}, "
          f"confidence={obs.confidence:.3f}")

# Test 3: Different signal types
print("\n3. Testing different signal types:")
for sig_type in ["continuous", "intermittent", "appearing", "disappearing"]:
    gt = generate_signal("R7", sig_type, seed=42)
    obs = create_observation(gt, "medium", 42)
    print(f"  {sig_type}: detected={obs.detected}, strength={obs.strength:.3f}")

# Test 4: Reproducibility
print("\n4. Testing reproducibility:")
gt = generate_signal("R7", "continuous", seed=42)
obs1 = create_observation(gt, "medium", 42)
obs2 = create_observation(gt, "medium", 42)
print(f"  Same seed (42): {obs1.strength:.3f} == {obs2.strength:.3f} → {obs1.strength == obs2.strength}")

obs3 = create_observation(gt, "medium", 43)
print(f"  Different seed (43): {obs1.strength:.3f} != {obs3.strength:.3f} → {obs1.strength != obs3.strength}")

# Test 5: Batch observations
print("\n5. Testing batch observations:")
ground_truths = [
    generate_signal("R1", "continuous", seed=1),
    generate_signal("R2", "intermittent", seed=2),
    generate_signal("R3", "appearing", seed=3),
]

model = ObservationModel(noise_level="medium", seed=42)
batch_obs = model.batch_observe(ground_truths)

for obs in batch_obs:
    print(f"  {obs.region_id}: detected={obs.detected}, strength={obs.strength:.3f}")

# Test 6: Critical distinction - Ground Truth vs Observation
print("\n6. CRITICAL DISTINCTION - GROUND TRUTH vs OBSERVATION:")
print("  This is why the AI cannot cheat!")
print("\n  Ground Truth (Hidden):")
gt = generate_signal("R7", "continuous", seed=42)
gt["strength"] = 0.85  # Strong signal
print(f"    Strength: {gt['strength']:.3f}")
print(f"    Signal Type: {gt['signal_type']}")

obs = create_observation(gt, "high", 42)
print("\n  Observation (What AI sees):")
print(f"    Detected: {obs.detected}")
print(f"    Strength: {obs.strength:.3f} (noisy, different from ground truth!)")
print(f"    Confidence: {obs.confidence:.3f}")

print("\n" + "=" * 60)
print("✅ OBSERVATION MODEL VERIFICATION COMPLETE!")
print("=" * 60)