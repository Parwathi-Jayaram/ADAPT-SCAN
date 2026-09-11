"""
verify_m2.py - Full M2 Pipeline Verification with Edge Cases
Run from repo root: python verify_m2.py
"""

import sys
import os
import time
from typing import Any, cast

# Ensure repo root is on path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"✅ {label}")
    else:
        FAIL += 1
        print(f"❌ {label} {detail}")


print("=" * 70)
print("M2 FULL PIPELINE VERIFICATION")
print("=" * 70)

# ============================================================
# SECTION 1: IMPORTS
# ============================================================
print("\n[1] IMPORTS")

try:
    from m2_signal.m2_interface import M2Interface, generate_observation, validate_scanner_result
    from m2_signal.m3_integration import M2M3Bridge, scan, scan_all
    check("Import M2Interface", True)
    check("Import M3 bridge", True)
except Exception as e:
    check("Import M2 modules", False, str(e))
    sys.exit(1)

# ============================================================
# SECTION 2: BASIC OBSERVATION
# ============================================================
print("\n[2] BASIC OBSERVATION")

m2 = M2Interface(noise_level="medium", seed=42)
obs = m2.generate_observation({"region_id": "R7"})

check("Returns dict", isinstance(obs, dict))
check("Has region_id", obs.get("region_id") == "R7")
check("Has detected", "detected" in obs and isinstance(obs["detected"], bool))
check("Has strength", "strength" in obs and 0.0 <= obs["strength"] <= 1.0)
check("Has bandwidth", "bandwidth" in obs and 0.0 <= obs["bandwidth"] <= 1.0)
check("Has snr", "snr" in obs)
check("Has confidence", "confidence" in obs and 0.0 <= obs["confidence"] <= 1.0)
check("Has confidence_level", obs.get("confidence_level") in
      ["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW"])
check("Has 8 features", isinstance(obs["features"], list) and len(obs["features"]) == 8)
check("All features 0-1", all(0.0 <= f <= 1.0 for f in obs["features"]))
check("Timestamp is float", isinstance(obs["timestamp"], float))
check("Has feature_meaning", isinstance(obs.get("feature_meaning"), dict))

# ============================================================
# SECTION 3: INTERNAL CONSISTENCY
# ============================================================
print("\n[3] INTERNAL CONSISTENCY")

# Feature[0] == confidence
check("features[0] == confidence",
      abs(obs["features"][0] - obs["confidence"]) < 0.001)

# Feature[1] == strength
check("features[1] == strength",
      abs(obs["features"][1] - obs["strength"]) < 0.001)

# Feature[2] == bandwidth
check("features[2] == bandwidth",
      abs(obs["features"][2] - obs["bandwidth"]) < 0.001)

# When detected=False, strength == 0 and confidence <= 0.2
obs_false = None
for region in ["R1", "R2", "R3", "R4", "R5", "R6", "R8", "R9", "R10"]:
    o = m2.generate_observation({"region_id": region})
    if not o["detected"]:
        obs_false = o
        break

if obs_false:
    check("No-detection strength == 0", obs_false["strength"] == 0.0)
    check("No-detection snr == 0", obs_false["snr"] == 0.0)
    check("No-detection confidence <= 0.2", obs_false["confidence"] <= 0.2)
    check("No-detection uncertainty low (features[4] <= 0.3)", obs_false["features"][4] <= 0.3)
else:
    print("ℹ️ No detection=False case found in samples (all detected)")

# ============================================================
# SECTION 4: CONFIDENCE LEVEL MATCHES CONFIDENCE
# ============================================================
print("\n[4] CONFIDENCE LEVEL MAPPING")

def expected_level(c):
    if c >= 0.9: return "VERY_HIGH"
    if c >= 0.7: return "HIGH"
    if c >= 0.5: return "MEDIUM"
    if c >= 0.3: return "LOW"
    return "VERY_LOW"

for region in ["R1", "R5", "R10", "R15"]:
    o = m2.generate_observation({"region_id": region})
    check(f"{region} confidence_level matches confidence",
          o["confidence_level"] == expected_level(o["confidence"]),
          f"(conf={o['confidence']:.3f}, level={o['confidence_level']})")

# ============================================================
# SECTION 5: TYPE VALIDATION (EDGE CASES)
# ============================================================
print("\n[5] TYPE VALIDATION EDGE CASES")

# Missing region_id
try:
    m2.generate_observation({})
    check("Missing region_id raises ValueError", False)
except ValueError:
    check("Missing region_id raises ValueError", True)

# Wrong type region_id
try:
    m2.generate_observation({"region_id": 123})
    check("Int region_id raises TypeError", False)
except TypeError:
    check("Int region_id raises TypeError", True)

# None region_id
try:
    m2.generate_observation({"region_id": None})
    check("None region_id raises TypeError", False)
except TypeError:
    check("None region_id raises TypeError", True)

# Invalid signal_type
try:
    m2.generate_observation({"region_id": "R7", "signal_type": "invalid"})
    check("Invalid signal_type raises ValueError", False)
except ValueError:
    check("Invalid signal_type raises ValueError", True)

# Invalid scan_mode
try:
    m2.generate_observation({"region_id": "R7", "scan_mode": "invalid"})
    check("Invalid scan_mode raises ValueError", False)
except ValueError:
    check("Invalid scan_mode raises ValueError", True)

# Negative additional_cost
try:
    m2.generate_observation({"region_id": "R7", "additional_cost": -1.0})
    check("Negative additional_cost raises ValueError", False)
except ValueError:
    check("Negative additional_cost raises ValueError", True)

# Non-dict input
try:
    m2.generate_observation("R7")  # type: ignore
    check("String input raises TypeError", False)
except TypeError:
    check("String input raises TypeError", True)

# ============================================================
# SECTION 6: NO-SIGNAL / MISSING OBSERVATION
# ============================================================
print("\n[6] NO-SIGNAL HANDLING")

no_sig = m2.handle_no_signal("R99")
check("No-signal detected == False", no_sig["detected"] == False)
check("No-signal strength == 0", no_sig["strength"] == 0.0)
check("No-signal snr == 0", no_sig["snr"] == 0.0)
check("No-signal confidence == 0", no_sig["confidence"] == 0.0)
check("No-signal has 8 features", len(no_sig["features"]) == 8)
check("No-signal timestamp is float", isinstance(no_sig["timestamp"], float))

# ============================================================
# SECTION 7: REPRODUCIBILITY
# ============================================================
print("\n[7] REPRODUCIBILITY")

m2a = M2Interface(noise_level="medium", seed=42)
m2b = M2Interface(noise_level="medium", seed=42)
o1 = m2a.generate_observation({"region_id": "R7"})
o2 = m2b.generate_observation({"region_id": "R7"})
check("Same seed → same detected", o1["detected"] == o2["detected"])
check("Same seed → same confidence", o1["confidence"] == o2["confidence"])
check("Same seed → same strength", o1["strength"] == o2["strength"])

# ============================================================
# SECTION 8: NOISE LEVELS
# ============================================================
print("\n[8] NOISE LEVELS")

for level in ["low", "medium", "high"]:
    m = M2Interface(noise_level=level, seed=42)
    o = m.generate_observation({"region_id": "R7"})
    check(f"{level} noise produces valid output",
          isinstance(o, dict) and "confidence" in o)

# ============================================================
# SECTION 9: M3 BRIDGE (MOCK MODE)
# ============================================================
print("\n[9] M3 BRIDGE - MOCK MODE")

bridge = M2M3Bridge(m3_available=False, seed=42)
check("Bridge initializes", bridge is not None)
check("m3_available == False", bridge.m3_available == False)

br_obs = bridge.scan_region("R7")
check("Bridge scan_region returns dict", isinstance(br_obs, dict))
check("Bridge output has region_id", br_obs.get("region_id") == "R7")
check("Bridge output has confidence_level", "confidence_level" in br_obs)
check("Bridge output has 8 features", len(br_obs["features"]) == 8)

# Multiple regions
multi = bridge.scan_multiple_regions(["R1", "R2", "R3"])
check("Multiple regions returns list", isinstance(multi, list))
check("Multiple regions returns 3", len(multi) == 3)
check("Each has region_id", all("region_id" in r for r in multi))

# Signal classification
check("_classify_signal returns string",
      isinstance(bridge._classify_signal(0.8, 0.3, 12.0), str))
check("_classify_signal handles zeros",
      isinstance(bridge._classify_signal(0.0, 0.0, 0.0), str))

# ============================================================
# SECTION 10: CONVENIENCE FUNCTIONS
# ============================================================
print("\n[10] CONVENIENCE FUNCTIONS")

s1 = scan("R7", seed=42)
check("scan() returns dict", isinstance(s1, dict))
check("scan() has region_id", s1.get("region_id") == "R7")

s2 = scan_all(["R1", "R2", "R3"], seed=42)
check("scan_all() returns list", isinstance(s2, list))
check("scan_all() returns 3 results", len(s2) == 3)

# ============================================================
# SECTION 11: EDGE CASES
# ============================================================
print("\n[11] EDGE CASES")

# Empty region list
empty = scan_all([], seed=42)
check("Empty region list returns empty list", empty == [])

# Large region list
large = scan_all([f"R{i}" for i in range(1, 21)], seed=42)
check("20 regions processed", len(large) == 20)

# Single-char region
single = scan("X", seed=42)
check("Single-char region works", single["region_id"] == "X")

# Long region name
long_name = "REGION_" + "X" * 50
long_obs = scan(long_name, seed=42)
check("Long region name works", long_obs["region_id"] == long_name)

# region_id with spaces
spaced = scan("Region 7", seed=42)
check("Region with spaces works", spaced["region_id"] == "Region 7")

# ============================================================
# SECTION 12: GROUND TRUTH SEPARATION
# ============================================================
print("\n[12] GROUND TRUTH SEPARATION")

obs_check = m2.generate_observation({"region_id": "R7"})
forbidden_keys = ["ground_truth", "truth", "actual_strength", "true_strength",
                  "is_real", "hidden", "exists"]
leaks = [k for k in forbidden_keys if k in obs_check]
check("No ground truth keys in output", len(leaks) == 0, f"Found: {leaks}")

# ============================================================
# SECTION 13: RANGE VALIDATION
# ============================================================
print("\n[13] ALL VALUES IN 0-1 RANGE")

for region in [f"R{i}" for i in range(1, 11)]:
    o = m2.generate_observation({"region_id": region})
    valid = (
        0.0 <= o["strength"] <= 1.0 and
        0.0 <= o["bandwidth"] <= 1.0 and
        0.0 <= o["confidence"] <= 1.0 and
        all(0.0 <= f <= 1.0 for f in o["features"])
    )
    if not valid:
        check(f"{region} all values in range", False,
              f"strength={o['strength']}, conf={o['confidence']}")
        break
else:
    check("All 10 regions have values in 0-1 range", True)

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"✅ Passed: {PASS}")
print(f"❌ Failed: {FAIL}")
print(f"Total:    {PASS + FAIL}")

if FAIL == 0:
    print("\n🎉 ALL CHECKS PASSED — M2 IS PRODUCTION READY!")
else:
    print(f"\n⚠️ {FAIL} CHECK(S) FAILED — REVIEW ABOVE")
print("=" * 70)