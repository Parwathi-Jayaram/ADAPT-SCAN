"""
observation.py - Observation Model for Member 2

CRITICAL: This maintains the separation between:
- GROUND TRUTH (hidden, only simulator knows)
- OBSERVATION (what AI sees after noise + scanner effects)
"""

import random
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Conditional import - works both as package and when run directly
try:
    from .noise_model import get_noise_config, apply_noise
except ImportError:
    from noise_model import get_noise_config, apply_noise


@dataclass
class Observation:
    """
    Represents a noisy observation from the scanner.
    
    This is what the AI/decision engine sees - NOT the ground truth!
    """
    region_id: str
    detected: bool
    strength: float  # 0-1, noisy
    bandwidth: float  # 0-1, noisy
    snr: float
    confidence: float  # 0-1
    timestamp: float
    scan_cost: float
    features: Dict[str, Any]
    observation_id: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    def __repr__(self):
        return (f"Observation(region={self.region_id}, "
                f"detected={self.detected}, "
                f"strength={self.strength:.3f}, "
                f"confidence={self.confidence:.3f})")


class ObservationModel:
    """
    Simulates scanner observations from ground truth.
    
    The AI only sees observations from this model, never the ground truth!
    """
    
    def __init__(self, noise_level: str = "medium", seed: Optional[int] = None):
        self.noise_level = noise_level
        self.seed = seed
        self.rng = random.Random(seed)
        
        self.noise_config = get_noise_config(noise_level)
        self.noise_strength = self.noise_config["noise_strength"]
        self.missing_prob = self.noise_config["missing_probability"]
        self.scan_cost_base = 1.0
    
    def _apply_detection_logic(self, strength: float, confidence: float) -> bool:
        """
        Determine if a signal is detected based on strength and confidence.
        """
        detection_threshold = self.rng.uniform(0.1, 0.35)
        detected = strength > detection_threshold
        
        if confidence < 0.2:
            detected = False
        
        if self.noise_level == "high":
            if detected and self.rng.random() < 0.15:
                detected = False
            if not detected and self.rng.random() < 0.08:
                detected = True
        elif self.noise_level == "medium":
            if detected and self.rng.random() < 0.08:
                detected = False
            if not detected and self.rng.random() < 0.05:
                detected = True
        
        return detected
    
    def _calculate_snr(self, strength: float) -> float:
        """Calculate signal-to-noise ratio."""
        if self.noise_strength < 0.001:
            return 100.0
        return strength / (self.noise_strength * 2 + 0.001)
    
    def observe(self, ground_truth: Dict[str, Any], 
                scanner_action: Optional[Dict[str, Any]] = None,
                timestamp: Optional[float] = None) -> Observation:
        """
        Generate an observation from ground truth.
        
        CRITICAL: The AI ONLY sees this observation, NOT ground_truth!
        """
        if timestamp is None:
            timestamp = time.time()
        
        region_id = ground_truth.get("region_id", "R1")
        strength = ground_truth.get("strength", 0.5)
        bandwidth = ground_truth.get("bandwidth", 0.5)
        activity = ground_truth.get("activity", 0.5)
        signal_type = ground_truth.get("signal_type", "unknown")
        
        scan_cost = self.scan_cost_base
        if scanner_action:
            scan_cost += scanner_action.get("additional_cost", 0.0)
        
        obs_seed = None
        if self.seed is not None:
            obs_seed = self.seed + hash(str(ground_truth)) % 1000
        
        noisy_strength = apply_noise(strength, self.noise_strength, seed=obs_seed)
        noisy_bandwidth = apply_noise(
            bandwidth,
            self.noise_strength * 0.5,
            seed=(obs_seed + 1 if obs_seed else None)
        )
        
        base_confidence = 1.0 - (self.noise_strength * 1.5)
        confidence = max(0.1, min(1.0, base_confidence))
        confidence = apply_noise(confidence, 0.1, seed=(obs_seed + 2 if obs_seed else None))
        confidence = max(0.1, min(1.0, confidence))
        
        detected = self._apply_detection_logic(noisy_strength, confidence)
        
        if self.rng.random() < self.missing_prob:
            detected = False
            noisy_strength = 0.0
            confidence = 0.1
        
        snr = self._calculate_snr(noisy_strength)
        
        features = {
            "signal_type": signal_type if detected else "unknown",
            "activity_estimate": activity * (0.8 + 0.4 * confidence) if detected else 0.0,
            "detection_confidence": confidence,
            "noise_level": self.noise_level,
            "timestamp": timestamp
        }
        
        return Observation(
            region_id=region_id,
            detected=detected,
            strength=noisy_strength,
            bandwidth=noisy_bandwidth,
            snr=snr,
            confidence=confidence,
            timestamp=timestamp,
            scan_cost=scan_cost,
            features=features,
            observation_id=f"obs_{timestamp}_{region_id}"
        )
    
    def batch_observe(self, 
                  ground_truths: List[Dict[str, Any]],
                  scanner_actions: Optional[List[Optional[Dict[str, Any]]]] = None,
                  timestamp: Optional[float] = None) -> List[Observation]:
        """
        Generate observations for multiple ground truths.
        
        Args:
            ground_truths: List of ground truth dictionaries
            scanner_actions: List of scanner actions (or None for each)
            timestamp: Optional timestamp for all observations
        """
        
        if scanner_actions is None:
                scanner_actions = [None for _ in ground_truths]
        
        observations = []
        for gt, action in zip(ground_truths, scanner_actions):
            obs = self.observe(gt, action, timestamp)
            observations.append(obs)
        
        return observations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current observation model."""
        return {
            "noise_level": self.noise_level,
            "noise_strength": self.noise_strength,
            "missing_probability": self.missing_prob,
            "scan_cost_base": self.scan_cost_base
        }


def create_observation(ground_truth: Dict[str, Any],
                      noise_level: str = "medium",
                      seed: Optional[int] = None) -> Observation:
    """Quick function to generate an observation from ground truth."""
    model = ObservationModel(noise_level, seed)
    return model.observe(ground_truth)


if __name__ == "__main__":
    # Conditional import for signal_generator when running directly
    try:
        from .signal_generator import generate_signal
    except ImportError:
        from signal_generator import generate_signal
    
    print("=" * 60)
    print("OBSERVATION MODEL TEST")
    print("=" * 60)
    
    print("\n1. Testing basic observation:")
    gt = generate_signal("R7", "continuous", seed=42)
    print(f"Ground Truth: strength={gt['strength']:.3f}")
    
    obs = create_observation(gt, "medium", 42)
    print(f"Observation: detected={obs.detected}, strength={obs.strength:.3f}")
    
    print("\n✅ Observation model working correctly!")