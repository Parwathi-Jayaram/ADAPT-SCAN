# tests/test_feature_extractor.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\tests\test_feature_extractor.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signal_generator import generate_signal
from observation import ObservationModel
from feature_extractor import FeatureExtractor, extract_features

print("=" * 60)
print("STEP 7: FEATURE EXTRACTOR VERIFICATION")
print("=" * 60)

# Test 1: Basic feature extraction
print("\n1. Testing basic feature extraction:")
gt = generate_signal("R7", "continuous", seed=42)
print(f"Ground Truth: strength={gt['strength']:.3f}, type={gt['signal_type']}")

obs_model = ObservationModel(noise_level="medium", seed=42)
obs = obs_model.observe(gt)
print(f"Observation: detected={obs.detected}, strength={obs.strength:.3f}")

features = extract_features(obs)
print(f"\nExtracted Features:")
print(f"  Region: {features.region_id}")
print(f"  Detection Confidence: {features.detection_confidence:.3f}")
print(f"  Strength Estimate: {features.strength_estimate:.3f}")
print(f"  Uncertainty: {features.uncertainty:.3f}")
print(f"  Reliability: {features.reliability:.3f}")
print(f"  History Length: {features.history_length}")
print(f"  Signal Type Probs: {features.signal_type_probs}")

# Test 2: Temporal features with multiple observations
print("\n2. Testing temporal features with multiple observations:")
extractor = FeatureExtractor(history_length=10)

print("Simulating 5 observations over time:")
for i in range(5):
    gt = generate_signal("R7", "continuous", seed=42 + i)
    # Vary strength over time
    gt["strength"] = 0.5 + (i * 0.08)
    
    obs = obs_model.observe(gt)
    features = extractor.extract(obs)
    
    print(f"  Step {i+1}: strength={features.strength_estimate:.3f}, "
          f"trend={features.temporal_features['trend']}, "
          f"stability={features.temporal_features['stability']:.3f}")

# Test 3: Different noise levels
print("\n3. Testing feature extraction with different noise levels:")
for noise_level in ["low", "medium", "high"]:
    gt = generate_signal("R7", "continuous", seed=42)
    obs_model = ObservationModel(noise_level=noise_level, seed=42)
    obs = obs_model.observe(gt)
    features = extract_features(obs)
    
    print(f"\n  {noise_level.upper()} NOISE:")
    print(f"    Detected: {obs.detected}")
    print(f"    Confidence: {features.detection_confidence:.3f}")
    print(f"    Uncertainty: {features.uncertainty:.3f}")
    print(f"    Reliability: {features.reliability:.3f}")

# Test 4: Region summary
print("\n4. Testing region summary:")
extractor = FeatureExtractor(history_length=10)

# Simulate multiple observations for region R7
for i in range(5):
    gt = generate_signal("R7", "intermittent", seed=42 + i)
    obs = obs_model.observe(gt)
    extractor.extract(obs)

# Simulate some observations for region R8
for i in range(3):
    gt = generate_signal("R8", "continuous", seed=100 + i)
    obs = obs_model.observe(gt)
    extractor.extract(obs)

summary = extractor.get_region_summary("R7")
print(f"\nRegion R7 Summary:")
for key, value in summary.items():
    if isinstance(value, float):
        print(f"  {key}: {value:.3f}")
    else:
        print(f"  {key}: {value}")

# Test 5: All regions summary
print("\n5. Testing all regions summary:")
all_summaries = extractor.get_all_region_summaries()
for region_id, summary in all_summaries.items():
    print(f"\n  {region_id}:")
    print(f"    Detected: {summary['detected']}")
    print(f"    Confidence: {summary['confidence']:.3f}")
    print(f"    Detection Rate: {summary['detection_rate']:.3f}")
    print(f"    Uncertainty: {summary['uncertainty']:.3f}")

# Test 6: Batch feature extraction
print("\n6. Testing batch feature extraction:")
ground_truths = [
    generate_signal("R1", "continuous", seed=1),
    generate_signal("R2", "intermittent", seed=2),
    generate_signal("R3", "appearing", seed=3),
]

obs_model = ObservationModel(noise_level="medium", seed=42)
batch_obs = obs_model.batch_observe(ground_truths)

extractor = FeatureExtractor()
batch_features = extractor.extract_batch(batch_obs)

for features in batch_features:
    print(f"  {features.region_id}: confidence={features.detection_confidence:.3f}, "
          f"uncertainty={features.uncertainty:.3f}")

print("\n" + "=" * 60)
print("✅ FEATURE EXTRACTOR VERIFICATION COMPLETE!")
print("=" * 60)