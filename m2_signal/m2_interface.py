"""
MEMBER 2 - REAL INTEGRATION INTERFACE
=====================================
This is the ACTUAL interface that M1 and M3 will use.

VERSION: 1.1.0
STATUS: ✅ Production Ready
"""

from typing import Dict, Any, Optional, List, Union
import time

# Conditional imports - works both as package and when run directly
try:
    from .signal_generator import generate_signal
    from .noise_model import get_noise_config, apply_noise
    from .observation import ObservationModel, Observation
    from .feature_extractor import FeatureExtractor
except ImportError:
    from signal_generator import generate_signal
    from noise_model import get_noise_config, apply_noise
    from observation import ObservationModel, Observation
    from feature_extractor import FeatureExtractor


# ============================================
# FEATURE DEFINITIONS
# ============================================

FEATURE_MEANINGS = {
    0: {
        "name": "detection_confidence",
        "description": "How confident we are in detection",
        "range": "0.0-1.0",
        "higher_is": "more confident"
    },
    1: {
        "name": "strength_estimate",
        "description": "Estimated signal strength",
        "range": "0.0-1.0",
        "higher_is": "stronger signal"
    },
    2: {
        "name": "bandwidth_estimate",
        "description": "Estimated signal bandwidth",
        "range": "0.0-1.0",
        "higher_is": "wider bandwidth"
    },
    3: {
        "name": "activity_estimate",
        "description": "Estimated signal activity level",
        "range": "0.0-1.0",
        "higher_is": "more active"
    },
    4: {
        "name": "uncertainty",
        "description": "How uncertain we are about this region",
        "range": "0.0-1.0",
        "higher_is": "more uncertain (need to scan)"
    },
    5: {
        "name": "reliability",
        "description": "How reliable are these features",
        "range": "0.0-1.0",
        "higher_is": "more reliable"
    },
    6: {
        "name": "stability",
        "description": "How stable the signal is over time",
        "range": "0.0-1.0",
        "higher_is": "more stable"
    },
    7: {
        "name": "change_rate",
        "description": "Rate of change in the signal",
        "range": "0.0-1.0",
        "higher_is": "changing faster"
    }
}


# ============================================
# VALIDATION FUNCTIONS
# ============================================

def validate_scanner_result(scanner_result: Dict[str, Any]) -> None:
    """Validate scanner_result before processing."""
    if not isinstance(scanner_result, dict):
        raise TypeError(
            f"scanner_result must be dict, got {type(scanner_result).__name__}"
        )
    
    if "region_id" not in scanner_result:
        raise ValueError("scanner_result must contain 'region_id'")
    
    if not isinstance(scanner_result["region_id"], str):
        raise TypeError(
            f"region_id must be str, got {type(scanner_result['region_id']).__name__}"
        )
    
    if "signal_type" in scanner_result:
        valid_types = [
            "continuous", "intermittent", "appearing", 
            "disappearing", "changing-strength", "noisy", "overlapping"
        ]
        if scanner_result["signal_type"] not in valid_types:
            raise ValueError(
                f"signal_type must be one of {valid_types}, "
                f"got '{scanner_result['signal_type']}'"
            )
    
    if "scan_mode" in scanner_result:
        valid_modes = ["standard", "high_resolution", "quick"]
        if scanner_result["scan_mode"] not in valid_modes:
            raise ValueError(
                f"scan_mode must be one of {valid_modes}, "
                f"got '{scanner_result['scan_mode']}'"
            )
    
    if "additional_cost" in scanner_result:
        if not isinstance(scanner_result["additional_cost"], (int, float)):
            raise TypeError(
                f"additional_cost must be number, "
                f"got {type(scanner_result['additional_cost']).__name__}"
            )
        if scanner_result["additional_cost"] < 0:
            raise ValueError("additional_cost cannot be negative")


# ============================================
# MAIN INTERFACE CLASS
# ============================================

class M2Interface:
    """REAL Interface for M2 - Signal Processing Module."""
    
    def __init__(self, 
                 noise_level: str = "medium",
                 seed: Optional[int] = None,
                 history_length: int = 10,
                 detection_threshold: float = 0.3):
        self.noise_level = noise_level
        self.seed = seed
        self.history_length = history_length
        self.detection_threshold = detection_threshold
        
        if not 0.05 <= detection_threshold <= 0.8:
            raise ValueError(
                f"detection_threshold must be between 0.05 and 0.8, "
                f"got {detection_threshold}"
            )
        
        self._observation_model = ObservationModel(noise_level, seed)
        self._feature_extractor = FeatureExtractor(history_length)
        
        self._region_histories = {}
        self._last_observations = {}
    
    def generate_observation(self, scanner_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate observation with full validation."""
        validate_scanner_result(scanner_result)
        
        region_id = scanner_result["region_id"]
        signal_type = scanner_result.get("signal_type", "continuous")
        scan_mode = scanner_result.get("scan_mode", "standard")
        additional_cost = scanner_result.get("additional_cost", 0.0)
        
        ground_truth = generate_signal(
            region_id=region_id,
            signal_type=signal_type,
            seed=self.seed
        )
        
        if scan_mode == "high_resolution":
            ground_truth["strength"] = min(1.0, ground_truth["strength"] * 1.1)
            additional_cost += 0.5
        elif scan_mode == "quick":
            ground_truth["strength"] = max(0.0, ground_truth["strength"] * 0.9)
            additional_cost -= 0.3
        
        scanner_action = {
            "region_id": region_id,
            "scan_mode": scan_mode,
            "additional_cost": additional_cost
        }
        
        observation = self._observation_model.observe(
            ground_truth=ground_truth,
            scanner_action=scanner_action
        )
        
        features = self._feature_extractor.extract(observation)
        
        confidence = observation.confidence
        if confidence >= 0.9:
            confidence_level = "VERY_HIGH"
        elif confidence >= 0.7:
            confidence_level = "HIGH"
        elif confidence >= 0.5:
            confidence_level = "MEDIUM"
        elif confidence >= 0.3:
            confidence_level = "LOW"
        else:
            confidence_level = "VERY_LOW"
        
        processed_observation = {
            "region_id": region_id,
            "detected": bool(observation.detected),
            "strength": float(observation.strength),
            "bandwidth": float(observation.bandwidth),
            "snr": float(observation.snr),
            "confidence": float(observation.confidence),
            "confidence_level": confidence_level,
            "features": self._extract_features_for_m1(features),
            "feature_meaning": FEATURE_MEANINGS,
            "timestamp": float(observation.timestamp)
        }
        
        self._region_histories.setdefault(region_id, []).append(processed_observation)
        self._last_observations[region_id] = processed_observation
        
        return processed_observation
    
    def _extract_features_for_m1(self, features) -> List[float]:
        """Extract numerical features for M1's decision engine."""
        return [
            float(features.detection_confidence),
            float(features.strength_estimate),
            float(features.bandwidth_estimate),
            float(features.activity_estimate),
            float(features.uncertainty),
            float(features.reliability),
            float(features.temporal_features.get('stability', 1.0)),
            float(features.temporal_features.get('change_rate', 0.0))
        ]
    
    def get_processed_observation(self, region_id: str) -> Optional[Dict[str, Any]]:
        return self._last_observations.get(region_id)
    
    def get_region_history(self, region_id: str) -> List[Dict[str, Any]]:
        return self._region_histories.get(region_id, [])
    
    def handle_no_signal(self, region_id: str) -> Dict[str, Any]:
        return {
            "region_id": region_id,
            "detected": False,
            "strength": 0.0,
            "bandwidth": 0.0,
            "snr": 0.0,
            "confidence": 0.0,
            "confidence_level": "VERY_LOW",
            "features": [0.0] * 8,
            "feature_meaning": FEATURE_MEANINGS,
            "timestamp": float(time.time())
        }
    
    def reset_region(self, region_id: Optional[str] = None):
        if region_id:
            self._region_histories[region_id] = []
            self._last_observations.pop(region_id, None)
            self._feature_extractor.reset(region_id)
        else:
            self._region_histories = {}
            self._last_observations = {}
            self._feature_extractor.reset()
    
    def get_detection_threshold(self) -> float:
        return float(self.detection_threshold)
    
    def set_detection_threshold(self, threshold: float) -> None:
        if not 0.05 <= threshold <= 0.8:
            raise ValueError(f"threshold must be between 0.05 and 0.8, got {threshold}")
        self.detection_threshold = threshold
    
    def get_confidence_interpretation(self, confidence: float) -> str:
        if confidence >= 0.9:
            return "VERY_HIGH - Trust this detection"
        elif confidence >= 0.7:
            return "HIGH - Likely correct"
        elif confidence >= 0.5:
            return "MEDIUM - Consider with caution"
        elif confidence >= 0.3:
            return "LOW - Probably uncertain"
        else:
            return "VERY_LOW - Don't trust"
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "noise_level": self.noise_level,
            "seed": self.seed,
            "history_length": self.history_length,
            "detection_threshold": self.detection_threshold,
            "regions_tracked": len(self._region_histories),
            "total_observations": sum(len(h) for h in self._region_histories.values())
        }


# ============================================
# CONVENIENCE FUNCTION FOR M3
# ============================================

def generate_observation(scanner_result: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for M3."""
    interface = M2Interface(noise_level="medium", seed=42)
    return interface.generate_observation(scanner_result)


if __name__ == "__main__":
    print("=" * 60)
    print("M2 INTERFACE - PRODUCTION READY (v1.1.0)")
    print("=" * 60)
    
    m2 = M2Interface(noise_level="medium", seed=42)
    
    observation = m2.generate_observation({
        "region_id": "R7",
        "signal_type": "continuous",
        "scan_mode": "standard"
    })
    
    print("\nM2 output to M1:")
    for key, value in observation.items():
        if key == "features":
            print(f"   features: [{len(value)} features]")
        elif key == "feature_meaning":
            print(f"   feature_meaning: {len(value)} meanings defined")
        else:
            print(f"   {key}: {value}")
    
    print("\n✅ M2 INTERFACE IS PRODUCTION READY!")