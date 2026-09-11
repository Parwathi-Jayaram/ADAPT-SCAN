"""
run_all_tests.py
Runs all M2 tests, continues past failures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import test_signal_generator
import test_noise_model
import test_observation
import test_feature_extractor
import test_interface
import test_m3_integration


def run_safe(func, label):
    try:
        func()
    except AssertionError as e:
        print(f"❌ {label} FAILED: {e}")
    except Exception as e:
        print(f"❌ {label} ERROR: {e}")


def run_all():
    print("=" * 60)
    print("M2 SIGNAL PROCESSING - FULL TEST SUITE")
    print("=" * 60)
    
    print("\n[1/6] Testing signal_generator...")
    for name in dir(test_signal_generator):
        if name.startswith("test_"):
            run_safe(getattr(test_signal_generator, name), name)
    
    print("\n[2/6] Testing noise_model...")
    for name in dir(test_noise_model):
        if name.startswith("test_"):
            run_safe(getattr(test_noise_model, name), name)
    
    print("\n[3/6] Testing observation...")
    for name in dir(test_observation):
        if name.startswith("test_"):
            run_safe(getattr(test_observation, name), name)
    
    print("\n[4/6] Testing feature_extractor...")
    for name in dir(test_feature_extractor):
        if name.startswith("test_"):
            run_safe(getattr(test_feature_extractor, name), name)
    
    print("\n[5/6] Testing m2_interface...")
    for name in dir(test_interface):
        if name.startswith("test_"):
            run_safe(getattr(test_interface, name), name)
    
    print("\n[6/6] Testing m3_integration...")
    for name in dir(test_m3_integration):
        if name.startswith("test_"):
            run_safe(getattr(test_m3_integration, name), name)
    
    print("\n" + "=" * 60)
    print("✅ Test run complete. Check above for any failures.")
    print("=" * 60)


if __name__ == "__main__":
    run_all()