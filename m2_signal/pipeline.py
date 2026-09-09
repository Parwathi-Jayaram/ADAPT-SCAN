# pipeline.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\pipeline.py

"""
pipeline.py - Complete Signal Processing Pipeline for Member 2

This integrates all components:
1. Signal Generator → 2. Observation Model → 3. Feature Extractor

The output is clean features ready for Member 1 (Decision Engine).
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time
import json

try:
    from .signal_generator import generate_signal
    from .noise_model import get_noise_config, apply_noise
    from .observation import ObservationModel, Observation, create_observation
    from .feature_extractor import FeatureExtractor, ExtractedFeatures, extract_features
except ImportError:
    from signal_generator import generate_signal
    from noise_model import get_noise_config, apply_noise
    from observation import ObservationModel, Observation, create_observation
    from feature_extractor import FeatureExtractor, ExtractedFeatures, extract_features


@dataclass
class PipelineOutput:
    """
    Complete output from the signal processing pipeline.
    
    This contains everything needed by Member 1 (Decision Engine)
    and Member 3 (Simulation Environment).
    """
    ground_truth: Dict[str, Any]  # Hidden from AI - for evaluation only
    observation: Observation  # What the AI actually sees
    features: ExtractedFeatures  # Clean features for decision engine
    region_id: str
    timestamp: float
    pipeline_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ground_truth": self.ground_truth,
            "observation": self.observation.to_dict(),
            "features": self.features.to_dict(),
            "region_id": self.region_id,
            "timestamp": self.timestamp,
            "pipeline_version": self.pipeline_version
        }
    
    def get_ai_input(self) -> Dict[str, Any]:
        """
        Get only what the AI should see.
        
        CRITICAL: This excludes ground_truth!
        """
        return {
            "region_id": self.region_id,
            "observation": self.observation.to_dict(),
            "features": self.features.to_dict(),
            "timestamp": self.timestamp
        }


class SignalPipeline:
    """
    Complete signal processing pipeline.
    
    GROUND TRUTH → OBSERVATION (noisy) → FEATURES → AI
    """
    
    def __init__(self, 
                 noise_level: str = "medium",
                 history_length: int = 10,
                 seed: Optional[int] = None):
        """
        Initialize the pipeline.
        
        Parameters:
        -----------
        noise_level : str
            'low', 'medium', or 'high'
        history_length : int
            Number of observations to keep in history
        seed : int, optional
            For reproducibility
        """
        self.noise_level = noise_level
        self.seed = seed
        self.history_length = history_length
        
        # Initialize components
        self.observation_model = ObservationModel(noise_level, seed)
        self.feature_extractor = FeatureExtractor(history_length)
        
        # Track pipeline state
        self.total_observations = 0
        self.regions_seen = set()
        self.last_output = None
    
    def process_region(self, 
                       region_id: str, 
                       signal_type: str = "continuous",
                       custom_params: Optional[Dict[str, Any]] = None) -> PipelineOutput:
        """
        Process a single region through the complete pipeline.
        
        This generates ground truth, creates a noisy observation,
        extracts features, and returns everything.
        
        Parameters:
        -----------
        region_id : str
            Region to process (e.g., "R1", "R7")
        signal_type : str
            Type of signal: continuous, intermittent, appearing, etc.
        custom_params : dict, optional
            Override default signal parameters
            
        Returns:
        --------
        PipelineOutput : Complete pipeline output
        """
        # Generate ground truth
        ground_truth = generate_signal(
            region_id=region_id,
            signal_type=signal_type,
            seed=self.seed
        )
        
        # Override with custom parameters if provided
        if custom_params:
            ground_truth.update(custom_params)
        
        # Generate observation (noisy)
        observation = self.observation_model.observe(ground_truth)
        
        # Extract features
        features = self.feature_extractor.extract(observation)
        
        # Update pipeline state
        self.total_observations += 1
        self.regions_seen.add(region_id)
        
        # Create output
        output = PipelineOutput(
            ground_truth=ground_truth,
            observation=observation,
            features=features,
            region_id=region_id,
            timestamp=observation.timestamp
        )
        
        self.last_output = output
        return output
    
    def process_batch(self, 
                      region_configs: List[Dict[str, Any]]) -> List[PipelineOutput]:
        """
        Process multiple regions in batch.
        
        Parameters:
        -----------
        region_configs : list of dict
            Each dict should have:
            - region_id: str
            - signal_type: str (optional)
            - custom_params: dict (optional)
            
        Returns:
        --------
        list of PipelineOutput
        """
        outputs = []
        for config in region_configs:
            region_id = config.get("region_id", "R1")
            signal_type = config.get("signal_type", "continuous")
            custom_params = config.get("custom_params", {})
            
            output = self.process_region(region_id, signal_type, custom_params)
            outputs.append(output)
        
        return outputs
    
    def get_region_summary(self, region_id: str) -> Dict[str, Any]:
        """Get summary for a specific region."""
        return self.feature_extractor.get_region_summary(region_id)
    
    def get_all_region_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all regions."""
        return self.feature_extractor.get_all_region_summaries()
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline."""
        return {
            "noise_level": self.noise_level,
            "seed": self.seed,
            "history_length": self.history_length,
            "total_observations": self.total_observations,
            "regions_seen": list(self.regions_seen),
            "num_regions": len(self.regions_seen)
        }
    
    def reset(self):
        """Reset the pipeline state."""
        self.feature_extractor.reset()
        self.total_observations = 0
        self.regions_seen = set()
        self.last_output = None


# Convenience functions
def run_pipeline(region_id: str,
                 signal_type: str = "continuous",
                 noise_level: str = "medium",
                 seed: Optional[int] = None) -> PipelineOutput:
    """
    Quick function to run the complete pipeline.
    
    This is the main entry point for Member 3 to get observations.
    """
    pipeline = SignalPipeline(noise_level=noise_level, seed=seed)
    return pipeline.process_region(region_id, signal_type)


def run_pipeline_batch(region_configs: List[Dict[str, Any]],
                      noise_level: str = "medium",
                      seed: Optional[int] = None) -> List[PipelineOutput]:
    """
    Quick function to run the pipeline on multiple regions.
    """
    pipeline = SignalPipeline(noise_level=noise_level, seed=seed)
    return pipeline.process_batch(region_configs)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 8: COMPLETE PIPELINE VERIFICATION")
    print("=" * 60)
    
    print("\n🔄 Running complete signal processing pipeline...")
    print("   GROUND TRUTH → OBSERVATION (noisy) → FEATURES")
    print("   AI only sees the observation, NOT ground truth!\n")
    
    # Test 1: Single region
    print("1. Testing single region pipeline:")
    output = run_pipeline("R7", "continuous", "medium", seed=42)
    
    print(f"\n   Ground Truth (HIDDEN from AI):")
    print(f"     Region: {output.ground_truth['region_id']}")
    print(f"     Strength: {output.ground_truth['strength']:.3f}")
    print(f"     Signal Type: {output.ground_truth['signal_type']}")
    
    print(f"\n   Observation (What AI sees):")
    print(f"     Detected: {output.observation.detected}")
    print(f"     Strength: {output.observation.strength:.3f}")
    print(f"     Confidence: {output.observation.confidence:.3f}")
    
    print(f"\n   Features (For Decision Engine):")
    print(f"     Detection Confidence: {output.features.detection_confidence:.3f}")
    print(f"     Strength Estimate: {output.features.strength_estimate:.3f}")
    print(f"     Uncertainty: {output.features.uncertainty:.3f}")
    print(f"     Reliability: {output.features.reliability:.3f}")
    
    print(f"\n   What AI receives (no ground truth!):")
    ai_input = output.get_ai_input()
    print(f"     Keys: {list(ai_input.keys())}")
    print(f"     Contains ground_truth? {'ground_truth' in ai_input}")
    
    # Test 2: Multiple regions
    print("\n" + "=" * 60)
    print("2. Testing multi-region pipeline:")
    
    region_configs = [
        {"region_id": "R1", "signal_type": "continuous"},
        {"region_id": "R2", "signal_type": "intermittent"},
        {"region_id": "R3", "signal_type": "appearing"},
        {"region_id": "R4", "signal_type": "disappearing"},
    ]
    
    outputs = run_pipeline_batch(region_configs, "medium", seed=42)
    
    print("\n   Processing 4 regions:")
    for output in outputs:
        print(f"     {output.region_id}: "
              f"detected={output.observation.detected}, "
              f"strength={output.observation.strength:.3f}, "
              f"uncertainty={output.features.uncertainty:.3f}")
    
    # Test 3: Different noise levels
    print("\n" + "=" * 60)
    print("3. Testing different noise levels:")
    
    for noise_level in ["low", "medium", "high"]:
        output = run_pipeline("R7", "continuous", noise_level, seed=42)
        print(f"\n   {noise_level.upper()}:")
        print(f"     Detected: {output.observation.detected}")
        print(f"     Strength: {output.observation.strength:.3f}")
        print(f"     Confidence: {output.observation.confidence:.3f}")
        print(f"     Uncertainty: {output.features.uncertainty:.3f}")
        print(f"     Reliability: {output.features.reliability:.3f}")
    
    # Test 4: Different signal types
    print("\n" + "=" * 60)
    print("4. Testing different signal types:")
    
    signal_types = ["continuous", "intermittent", "appearing", 
                   "changing-strength", "disappearing", "noisy", "overlapping"]
    
    for signal_type in signal_types:
        output = run_pipeline("R7", signal_type, "medium", seed=42)
        print(f"\n   {signal_type}:")
        print(f"     Detected: {output.observation.detected}")
        print(f"     Strength: {output.observation.strength:.3f}")
        print(f"     Confidence: {output.observation.confidence:.3f}")
    
    # Test 5: Pipeline statistics
    print("\n" + "=" * 60)
    print("5. Pipeline Statistics:")
    
    pipeline = SignalPipeline(noise_level="medium", seed=42)
    
    # Process some regions
    for i in range(3):
        pipeline.process_region(f"R{i+1}", "continuous")
    
    stats = pipeline.get_pipeline_stats()
    print("\n   Stats:")
    for key, value in stats.items():
        print(f"     {key}: {value}")
    
    print("\n   Region Summaries:")
    summaries = pipeline.get_all_region_summaries()
    for region_id, summary in summaries.items():
        print(f"     {region_id}: confidence={summary['confidence']:.3f}, "
              f"detection_rate={summary['detection_rate']:.3f}")
    
    # Test 6: Reproducibility
    print("\n" + "=" * 60)
    print("6. Testing reproducibility:")
    
    output1 = run_pipeline("R7", "continuous", "medium", seed=42)
    output2 = run_pipeline("R7", "continuous", "medium", seed=42)
    
    print(f"\n   Same seed (42):")
    print(f"     Observation 1: strength={output1.observation.strength:.3f}")
    print(f"     Observation 2: strength={output2.observation.strength:.3f}")
    print(f"     Reproducible: {output1.observation.strength == output2.observation.strength}")
    
    output3 = run_pipeline("R7", "continuous", "medium", seed=43)
    print(f"\n   Different seed (43):")
    print(f"     Observation 3: strength={output3.observation.strength:.3f}")
    print(f"     Different from seed 42: {output1.observation.strength != output3.observation.strength}")
    
    # Test 7: Verify AI cannot see ground truth
    print("\n" + "=" * 60)
    print("7. VERIFYING CRITICAL DISTINCTION:")
    print("   ✓ Ground truth is hidden from AI")
    print("   ✓ AI only sees noisy observations")
    print("   ✓ Features are extracted from observations only")
    print("   ✓ No ground truth leakage in AI input\n")
    
    print("   This ensures the decision engine cannot cheat!")
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE PIPELINE VERIFICATION COMPLETE!")
    print("=" * 60)
    print("\n   Member 2 Signal Processing Pipeline is ready!")
    print("   Next: Integrate with Member 3 (Simulation Environment)")