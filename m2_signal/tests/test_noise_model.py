# test_noise_model.py
# Run this to verify your noise model
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
from noise_model import get_noise_config, apply_noise

print("=" * 60)
print("STEP 5: NOISE MODEL VERIFICATION")
print("=" * 60)

# Test 1: Verify noise configurations
print("\n1. Checking noise configurations:")
for level in ["low", "medium", "high"]:
    config = get_noise_config(level)
    print(f"  {level}: noise_strength={config['noise_strength']}, "
          f"missing_prob={config['missing_probability']}")

# Test 2: Verify noise application
print("\n2. Testing noise application (value=0.8):")
for level in ["low", "medium", "high"]:
    config = get_noise_config(level)
    noisy = apply_noise(0.8, config["noise_strength"], seed=42)
    print(f"  {level}: {noisy:.4f}")

# Test 3: Verify reproducibility
print("\n3. Testing reproducibility:")
value = 0.8
noisy1 = apply_noise(value, 0.15, seed=42)
noisy2 = apply_noise(value, 0.15, seed=42)
noisy3 = apply_noise(value, 0.15, seed=43)
print(f"  Same seed (42): {noisy1:.4f} == {noisy2:.4f} → {noisy1 == noisy2}")
print(f"  Different seed (43): {noisy1:.4f} != {noisy3:.4f} → {noisy1 != noisy3}")

# Test 4: Check clamping
print("\n4. Testing value clamping (should stay in [0,1]):")
test_values = [0.0, 0.5, 1.0]
for val in test_values:
    noisy = apply_noise(val, 0.3, seed=42)
    print(f"  {val} → {noisy:.4f} (clamped to [0,1])")