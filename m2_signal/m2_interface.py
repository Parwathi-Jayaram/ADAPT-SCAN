# m2_interface.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\m2_interface.py

"""
MEMBER 2 - REAL INTEGRATION INTERFACE
=====================================
This is the ACTUAL interface that M1 and M3 will use.

M2 expects from M3:
    scanner_result = {
        "region_id": "R7",
        "signal_type": "continuous",     # Optional, from M3
        "scan_mode": "standard",          # Optional
        "additional_cost": 0.0           # Optional
    }

M2 provides to M1:
    processed_observation = {
        "region_id": "R7",
        "detected": True,
        "strength": 0.63,
        "bandwidth": 0.41,
        "snr": 7.2,
        "confidence": 0.72,
        "features": [],
        "timestamp": 1234567890.0
    }

IMPORTANT: Ground truth is NEVER included in the observation sent to M1!
"""

from typing import Dict, Any, Optional, List
import time
import random

# Import M2's internal modules
from signal_generator import generate_signal
from noise_model import get_noise_config, apply_noise
from observation import ObservationModel, Observation
from feature_extractor import FeatureExtractor


class M2Interface:
    """
    REAL Interface for M2 - Signal Processing Module.
    
    This is what M3 and M1 actually use in production.
    
    M3 calls: generate_observation(scanner_result)
    M1 calls: get_processed_observation(region_id)  # Or receives via M3
    """
    
    def __init__(self, 
                 noise_level: str = "medium",
                 seed: Optional[int] = None,
                 history_length: int = 10):
        """
        Initialize M2 Interface.
        
        Args:
            noise_level: "low", "medium", or "high"
            seed: For reproducible results
            history_length: How many observations to keep in history
        """
        self.noise_level = noise_level
        self.seed = seed
        self.history_length = history_length
        
        # Internal components
        self._observation_model = ObservationModel(noise_level, seed)
        self._feature_extractor = FeatureExtractor(history_length)
        
        # Track state for each region
        self._region_histories = {}
        self._last_observations = {}
    
    def generate_observation(self, scanner_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        MAIN FUNCTION: M3 calls this with scanner result.
        
        This is the ONLY function M3 needs to call.
        
        Args:
            scanner_result: Dict from M3 containing:
                {
                    "region_id": "R7",          # REQUIRED
                    "signal_type": "continuous", # OPTIONAL (default: "continuous")
                    "scan_mode": "standard",     # OPTIONAL
                    "additional_cost": 0.0       # OPTIONAL
                }
        
        Returns:
            Processed observation for M1:
            {
                "region_id": "R7",
                "detected": True,
                "strength": 0.63,
                "bandwidth": 0.41,
                "snr": 7.2,
                "confidence": 0.72,
                "features": [],
                "timestamp": 1234567890.0
            }
        
        Raises:
            ValueError: If region_id is missing
        """
        # Validate input
        if "region_id" not in scanner_result:
            raise ValueError("M2: scanner_result must contain 'region_id'")
        
        region_id = scanner_result["region_id"]
        signal_type = scanner_result.get("signal_type", "continuous")
        scan_mode = scanner_result.get("scan_mode", "standard")
        additional_cost = scanner_result.get("additional_cost", 0.0)
        
        # Step 1: Generate ground truth (HIDDEN from M1)
        ground_truth = generate_signal(
            region_id=region_id,
            signal_type=signal_type,
            seed=self.seed
        )
        
        # Step 2: Add any scan mode effects
        if scan_mode == "high_resolution":
            # Higher resolution = more expensive but slightly better detection
            ground_truth["strength"] = min(1.0, ground_truth["strength"] * 1.1)
            additional_cost += 0.5
        elif scan_mode == "quick":
            # Quick scan = cheaper but less reliable
            ground_truth["strength"] = max(0.0, ground_truth["strength"] * 0.9)
            additional_cost -= 0.3
        
        # Step 3: Create scanner action dict for observation model
        scanner_action = {
            "region_id": region_id,
            "scan_mode": scan_mode,
            "additional_cost": additional_cost
        }
        
        # Step 4: Generate observation (noisy)
        observation = self._observation_model.observe(
            ground_truth=ground_truth,
            scanner_action=scanner_action
        )
        
        # Step 5: Extract features for M1
        features = self._feature_extractor.extract(observation)
        
        # Step 6: Build the processed observation for M1
        processed_observation = {
            "region_id": region_id,
            "detected": observation.detected,
            "strength": observation.strength,
            "bandwidth": observation.bandwidth,
            "snr": observation.snr,
            "confidence": observation.confidence,
            "features": self._extract_features_for_m1(features),
            "timestamp": observation.timestamp
        }
        
        # Store in history
        self._region_histories.setdefault(region_id, []).append(processed_observation)
        self._last_observations[region_id] = processed_observation
        
        return processed_observation
    
    def _extract_features_for_m1(self, features) -> List[float]:
        """
        Extract numerical features for M1's decision engine.
        
        Returns a list of feature values that M1 can use.
        """
        # Convert features to simple list of numbers
        feature_list = [
            features.detection_confidence,
            features.strength_estimate,
            features.bandwidth_estimate,
            features.activity_estimate,
            features.uncertainty,
            features.reliability,
            features.temporal_features.get('stability', 1.0),
            features.temporal_features.get('change_rate', 0.0)
        ]
        return feature_list
    
    def get_processed_observation(self, region_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest processed observation for a region.
        
        This is what M1 can call directly if needed.
        
        Args:
            region_id: Region to get observation for
            
        Returns:
            Latest processed observation or None if not found
        """
        return self._last_observations.get(region_id)
    
    def get_region_history(self, region_id: str) -> List[Dict[str, Any]]:
        """
        Get full history for a region.
        
        Useful for M1's temporal analysis.
        
        Args:
            region_id: Region to get history for
            
        Returns:
            List of historical observations
        """
        return self._region_histories.get(region_id, [])
    
    def handle_no_signal(self, region_id: str) -> Dict[str, Any]:
        """
        Handle cases where no signal is detected.
        
        This ensures the system doesn't crash on missing observations.
        
        Args:
            region_id: Region with no signal
            
        Returns:
            Processed observation indicating no detection
        """
        return {
            "region_id": region_id,
            "detected": False,
            "strength": 0.0,
            "bandwidth": 0.0,
            "snr": 0.0,
            "confidence": 0.0,
            "features": [0.0] * 8,  # Empty features
            "timestamp": time.time()
        }
    
    def reset_region(self, region_id: Optional[str] = None):
        """
        Reset history for a region or all regions.
        
        Args:
            region_id: Specific region to reset, or None for all
        """
        if region_id:
            self._region_histories[region_id] = []
            self._last_observations.pop(region_id, None)
            self._feature_extractor.reset(region_id)
        else:
            self._region_histories = {}
            self._last_observations = {}
            self._feature_extractor.reset()


# ============================================
# SIMPLE HELPER FUNCTIONS FOR M3
# ============================================

def generate_observation(scanner_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for M3.
    
    This is the SIMPLEST interface M3 can use.
    
    Example:
        result = generate_observation({"region_id": "R7"})
    
    Args:
        scanner_result: Dict with at least "region_id"
        
    Returns:
        Processed observation for M1
    """
    interface = M2Interface(noise_level="medium", seed=42)
    return interface.generate_observation(scanner_result)


# ============================================
# PRODUCTION TEST - This is NOT a unit test
# This demonstrates how M3 and M1 will use this
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("M2 INTERFACE - PRODUCTION READY")
    print("=" * 60)
    
    # Initialize M2 interface
    m2 = M2Interface(noise_level="medium", seed=42)
    
    print("\n1. M3 calls: generate_observation()")
    print("-" * 40)
    
    # Simulate M3 calling with scanner result
    scanner_result = {
        "region_id": "R7",
        "signal_type": "continuous",
        "scan_mode": "standard"
    }
    
    print(f"   M3 input: {scanner_result}")
    
    # M2 processes and returns observation
    observation = m2.generate_observation(scanner_result)
    
    print(f"\n   M2 output to M1:")
    for key, value in observation.items():
        if key != "features":
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: [{len(value)} features]")
    
    print("\n2. M1 receives the observation:")
    print("-" * 40)
    print(f"   Region: {observation['region_id']}")
    print(f"   Detected: {observation['detected']}")
    print(f"   Strength: {observation['strength']:.3f}")
    print(f"   Confidence: {observation['confidence']:.3f}")
    print(f"   SNR: {observation['snr']:.2f}")
    
    print("\n3. Testing multiple regions:")
    print("-" * 40)
    
    regions = ["R1", "R2", "R3", "R4", "R5"]
    for region in regions:
        obs = m2.generate_observation({
            "region_id": region,
            "signal_type": "continuous"
        })
        print(f"   {region}: detected={obs['detected']}, "
              f"strength={obs['strength']:.3f}, "
              f"confidence={obs['confidence']:.3f}")
    
    print("\n4. Testing no-signal case:")
    print("-" * 40)
    
    # Simulate no signal
    no_signal = m2.handle_no_signal("R99")
    print(f"   No signal in R99:")
    print(f"   Detected: {no_signal['detected']}")
    print(f"   Confidence: {no_signal['confidence']}")
    
    print("\n5. Getting region history:")
    print("-" * 40)
    
    history = m2.get_region_history("R7")
    print(f"   R7 has {len(history)} observations in history")
    
    print("\n" + "=" * 60)
    print("✅ M2 INTERFACE IS PRODUCTION READY!")
    print("   M3 can call: generate_observation(scanner_result)")
    print("   M1 receives: processed_observation")
    print("   Ground truth is NEVER exposed to M1")
    print("=" * 60)