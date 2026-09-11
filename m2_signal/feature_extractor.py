# feature_extractor.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\feature_extractor.py

"""
feature_extractor.py - Feature Extraction for Member 2

Extracts useful features from observations for the belief engine.
This is the bridge between raw observations and the decision engine.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import random
import time


@dataclass
class ExtractedFeatures:
    """
    Clean feature representation for the belief engine.
    
    This is what gets passed to Member 1 (Decision Engine).
    """
    region_id: str
    detection_confidence: float  # 0-1
    strength_estimate: float  # 0-1
    bandwidth_estimate: float  # 0-1
    activity_estimate: float  # 0-1
    signal_type_probs: Dict[str, float]  # Probability distribution over signal types
    temporal_features: Dict[str, Any]  # Trend, stability, etc.
    uncertainty: float  # 0-1, how uncertain we are about this region
    reliability: float  # 0-1, how reliable these features are
    timestamp: float
    history_length: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return asdict(self)
    
    def __repr__(self):
        return (f"ExtractedFeatures(region={self.region_id}, "
                f"confidence={self.detection_confidence:.3f}, "
                f"strength={self.strength_estimate:.3f}, "
                f"uncertainty={self.uncertainty:.3f})")


class FeatureExtractor:
    """
    Extracts clean features from raw observations.
    
    This transforms scanner observations into features usable by the belief engine.
    Maintains history to extract temporal patterns.
    """
    
    def __init__(self, history_length: int = 10, decay_factor: float = 0.9):
        """
        Initialize feature extractor.
        
        Parameters:
        -----------
        history_length : int
            Number of past observations to keep for temporal features
        decay_factor : float
            How much to weight recent observations (0-1)
        """
        self.history_length = history_length
        self.decay_factor = decay_factor
        self.observation_history: Dict[str, deque] = {}  # region_id -> deque of observations
        self.feature_history: Dict[str, deque] = {}  # region_id -> deque of features
        
    def _initialize_history(self, region_id: str):
        """Initialize history for a region if not present."""
        if region_id not in self.observation_history:
            self.observation_history[region_id] = deque(maxlen=self.history_length)
            self.feature_history[region_id] = deque(maxlen=self.history_length)
    
    def _add_to_history(self, observation, features):
        """Add observation and features to history."""
        region_id = observation.region_id
        self._initialize_history(region_id)
        self.observation_history[region_id].append(observation)
        self.feature_history[region_id].append(features)
    
    def _calculate_uncertainty(self, observation, history_length: int) -> float:
        """
        Calculate uncertainty for this observation.
        
        High uncertainty when:
        - Observation confidence is low
        - Signal is weak / intermittent
        - History is inconsistent
        
        Low uncertainty when:
        - No signal detected (we are confident it is empty)
        - High confidence detection
        """
        # ✅ FIX: If not detected, uncertainty should be low (we are sure it is empty)
        if not observation.detected:
            return 0.1
        
        # Base uncertainty from confidence
        base_uncertainty = 1.0 - observation.confidence
        
        # Add uncertainty for weak signals
        if observation.strength < 0.3:
            base_uncertainty += 0.2
        
        # Add uncertainty from noise level
        noise_level = observation.features.get("noise_level", "medium")
        if noise_level == "high":
            base_uncertainty += 0.2
        elif noise_level == "low":
            base_uncertainty -= 0.1
        
        # Normalize to 0-1
        return max(0.0, min(1.0, base_uncertainty))
    
    def _extract_temporal_features(self, history: List) -> Dict[str, Any]:
        """
        Extract temporal features from observation history.
        """
        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "stability": 1.0,
                "change_rate": 0.0,
                "detection_stability": 1.0,
                "history_length": len(history)
            }
        
        # Calculate strength trend
        strengths = [obs.strength for obs in history]
        
        if len(strengths) >= 3:
            # Use weighted average for trend detection
            weights = [self.decay_factor ** i for i in range(len(strengths) - 1, -1, -1)]
            weighted_strengths = [s * w for s, w in zip(strengths, weights)]
            
            # Simple trend detection using first third vs last third
            n = len(strengths)
            first_third = np.mean(strengths[:max(1, n//3)])
            last_third = np.mean(strengths[-max(1, n//3):])
            
            if last_third > first_third * 1.15:
                trend = "increasing"
            elif last_third < first_third * 0.85:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Calculate stability (inverse of variance)
        if len(strengths) >= 3:
            variance = np.var(strengths)
            stability = 1.0 / (1.0 + variance * 10)
        else:
            stability = 1.0
        
        # Change rate (recent change)
        if len(strengths) >= 2:
            change_rate = abs(strengths[-1] - strengths[-2])
        else:
            change_rate = 0.0
        
        # Detection stability (how consistent are detections)
        detections = [1 if obs.detected else 0 for obs in history]
        detection_stability = np.mean(detections) if detections else 1.0
        
        return {
            "trend": trend,
            "stability": round(stability, 3),
            "change_rate": round(change_rate, 3),
            "detection_stability": round(detection_stability, 3),
            "history_length": len(history),
            "avg_strength": round(np.mean(strengths), 3)
        }
    
    def _estimate_signal_type_probs(self, observation) -> Dict[str, float]:
        """
        Estimate probability distribution over signal types.
        """
        all_types = ["continuous", "intermittent", "appearing", 
                    "changing-strength", "disappearing", "noisy", "overlapping"]
        
        if not observation.detected:
            # No detection: low probabilities for all
            probs = {t: 0.05 for t in all_types}
            probs["none"] = 0.65
            return probs
        
        # Use detected signal type from features
        detected_type = observation.features.get("signal_type", "unknown")
        
        if detected_type != "unknown":
            # High confidence for detected type
            base_prob = observation.confidence * 0.8
            probs = {t: 0.0 for t in all_types}
            probs[detected_type] = base_prob
            
            # Distribute remaining probability among other types
            remaining = 1.0 - base_prob
            other_types = [t for t in all_types if t != detected_type]
            if other_types:
                prob_per_type = remaining / len(other_types)
                for t in other_types:
                    probs[t] = prob_per_type
        else:
            # Unknown: uniform distribution
            prob_per_type = 0.8 / len(all_types)
            probs = {t: prob_per_type for t in all_types}
        
        # Normalize
        total = sum(probs.values())
        if total > 0:
            for t in probs:
                probs[t] /= total
        
        return probs
    
    def extract(self, observation) -> ExtractedFeatures:
        """
        Extract features from a single observation.
        
        Parameters:
        -----------
        observation : Observation
            Raw observation from the scanner
            
        Returns:
        --------
        ExtractedFeatures : Clean features for the belief engine
        """
        region_id = observation.region_id
        
        # Initialize history if needed
        self._initialize_history(region_id)
        
        # Calculate uncertainty
        history_len = len(self.observation_history[region_id])
        uncertainty = self._calculate_uncertainty(observation, history_len)
        
        # Get history for temporal features
        history_list = list(self.observation_history[region_id])
        
        # Extract temporal features
        temporal_features = self._extract_temporal_features(history_list)
        
        # Estimate signal type probabilities
        signal_type_probs = self._estimate_signal_type_probs(observation)
        
        # Calculate reliability (how much to trust these features)
        reliability = observation.confidence * (1.0 - uncertainty * 0.5)
        reliability = max(0.0, min(1.0, reliability))
        
        # Create extracted features
        features = ExtractedFeatures(
            region_id=region_id,
            detection_confidence=observation.confidence,
            strength_estimate=observation.strength,
            bandwidth_estimate=observation.bandwidth,
            activity_estimate=observation.features.get("activity_estimate", 0.5),
            signal_type_probs=signal_type_probs,
            temporal_features=temporal_features,
            uncertainty=uncertainty,
            reliability=reliability,
            timestamp=observation.timestamp,
            history_length=len(history_list)
        )
        
        # Add to history
        self._add_to_history(observation, features)
        
        return features
    
    def extract_batch(self, observations: List) -> List[ExtractedFeatures]:
        """Extract features from multiple observations."""
        return [self.extract(obs) for obs in observations]
    
    def get_region_summary(self, region_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a region based on its history.
        
        Useful for the belief engine to maintain state.
        """
        history = self.observation_history.get(region_id, deque())
        
        if not history:
            return {
                "region_id": region_id,
                "detected": False,
                "confidence": 0.0,
                "strength": 0.0,
                "last_seen": None,
                "history_length": 0,
                "detection_rate": 0.0
            }
        
        # Latest observation
        latest = history[-1]
        
        # Average strength
        avg_strength = np.mean([obs.strength for obs in history])
        
        # Detection rate
        detection_rate = sum([1 for obs in history if obs.detected]) / len(history)
        
        # Get latest features if available
        feature_history = self.feature_history.get(region_id, deque())
        latest_features = feature_history[-1] if feature_history else None
        
        return {
            "region_id": region_id,
            "detected": latest.detected,
            "confidence": latest.confidence,
            "strength": latest.strength,
            "avg_strength": avg_strength,
            "detection_rate": detection_rate,
            "last_seen": latest.timestamp,
            "history_length": len(history),
            "uncertainty": latest_features.uncertainty if latest_features else 0.5,
            "reliability": latest_features.reliability if latest_features else 0.5,
            "trend": self._extract_temporal_features(list(history))["trend"]
        }
    
    def reset(self, region_id: Optional[str] = None):
        """Reset history for a specific region or all regions."""
        if region_id:
            self.observation_history[region_id] = deque(maxlen=self.history_length)
            self.feature_history[region_id] = deque(maxlen=self.history_length)
        else:
            self.observation_history = {}
            self.feature_history = {}
    
    def get_all_region_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all regions."""
        summaries = {}
        for region_id in self.observation_history.keys():
            summaries[region_id] = self.get_region_summary(region_id)
        return summaries


# Convenience function
def extract_features(observation) -> ExtractedFeatures:
    """Quick function to extract features from an observation."""
    extractor = FeatureExtractor()
    return extractor.extract(observation)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 7: FEATURE EXTRACTOR READY")
    print("=" * 60)
    print("\nThis module is ready for testing.")
    print("Run: python tests/test_feature_extractor.py")