# difficult_scenarios.py
# Place this in: C:\Users\Acer\Desktop\m2_signal\difficult_scenarios.py

"""
difficult_scenarios.py - Difficult Test Scenarios for Member 2

Tests challenging cases that the adaptive scanning system must handle:
- Intermittent signals
- Sudden appearances/disappearances
- Weak signals in high noise
- Rapidly changing signals
- Overlapping/confusing signals
- Missing observations
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import random

try:
    from .signal_generator import generate_signal
    from .observation import ObservationModel
    from .feature_extractor import FeatureExtractor
    from .pipeline import SignalPipeline, PipelineOutput
except ImportError:
    from signal_generator import generate_signal
    from observation import ObservationModel
    from feature_extractor import FeatureExtractor
    from pipeline import SignalPipeline, PipelineOutput


@dataclass
class ScenarioResult:
    """Result of running a difficult scenario."""
    scenario_name: str
    success: bool
    detection_rate: float
    avg_confidence: float
    avg_uncertainty: float
    avg_reliability: float
    details: Dict[str, Any]
    
    def __repr__(self):
        return (f"ScenarioResult({self.scenario_name}, "
                f"detection_rate={self.detection_rate:.2f}, "
                f"success={self.success})")


class DifficultScenarioTester:
    """
    Tests the pipeline on difficult scenarios.
    
    These scenarios simulate real-world challenges:
    - Intermittent signals (appear/disappear)
    - Weak signals in high noise
    - Rapidly changing signals
    - Signal type changes
    """
    
    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.results: List[ScenarioResult] = []
    
    def _run_sequence(self, 
                      signal_configs: List[Dict[str, Any]], 
                      noise_level: str = "medium",
                      region_id: str = "R7") -> Dict[str, Any]:
        """
        Run a sequence of signal configurations and track results.
        """
        # Initialize pipeline
        pipeline = SignalPipeline(noise_level=noise_level, seed=self.seed)
        
        # Track results
        detections = []
        confidences = []
        uncertainties = []
        reliabilities = []
        strengths = []
        
        # Process each signal configuration
        for config in signal_configs:
            signal_type = config.get("signal_type", "continuous")
            custom_params = config.get("custom_params", {})
            
            # Process the region
            output = pipeline.process_region(
                region_id=region_id,
                signal_type=signal_type,
                custom_params=custom_params
            )
            
            # Record results
            detections.append(1 if output.observation.detected else 0)
            confidences.append(output.observation.confidence)
            uncertainties.append(output.features.uncertainty)
            reliabilities.append(output.features.reliability)
            strengths.append(output.observation.strength)
        
        # Calculate statistics
        return {
            "detection_rate": sum(detections) / len(detections) if detections else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "avg_uncertainty": sum(uncertainties) / len(uncertainties) if uncertainties else 0,
            "avg_reliability": sum(reliabilities) / len(reliabilities) if reliabilities else 0,
            "avg_strength": sum(strengths) / len(strengths) if strengths else 0,
            "num_steps": len(detections),
            "detections": detections,
            "confidences": confidences,
            "uncertainties": uncertainties
        }
    
    def scenario_intermittent_signal(self) -> ScenarioResult:
        """
        Scenario: Signal appears and disappears multiple times.
        
        Challenge: System must track intermittent emitters.
        """
        print("\n  🔄 Testing Intermittent Signal...")
        
        # Create sequence: ON, OFF, ON, OFF, ON
        configs = []
        for i in range(10):
            # Alternate between continuous (ON) and disappearing (OFF)
            if i % 2 == 0:
                configs.append({
                    "signal_type": "continuous",
                    "custom_params": {"strength": 0.7}
                })
            else:
                configs.append({
                    "signal_type": "disappearing",
                    "custom_params": {"strength": 0.7, "end_time": 0.5}
                })
        
        results = self._run_sequence(configs, "medium")
        
        success = results["detection_rate"] > 0.4  # Should detect at least some
        return ScenarioResult(
            scenario_name="intermittent_signal",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_sudden_appearance(self) -> ScenarioResult:
        """
        Scenario: Signal suddenly appears with high importance.
        
        Challenge: System must detect new emitters quickly.
        """
        print("\n  🚀 Testing Sudden Appearance...")
        
        # Create sequence: nothing, nothing, SUDDEN STRONG SIGNAL
        configs = []
        
        # First 5 steps: weak/no signal
        for i in range(5):
            configs.append({
                "signal_type": "continuous",
                "custom_params": {"strength": 0.1}
            })
        
        # Next 5 steps: strong signal appears
        for i in range(5):
            configs.append({
                "signal_type": "continuous",
                "custom_params": {"strength": 0.85}
            })
        
        results = self._run_sequence(configs, "medium")
        
        # Check if detection improved after appearance
        detections = results["detections"]
        if len(detections) >= 10:
            early_detections = sum(detections[:5])
            late_detections = sum(detections[5:])
            success = late_detections > early_detections
        else:
            success = results["detection_rate"] > 0.3
        
        return ScenarioResult(
            scenario_name="sudden_appearance",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_weak_signal_high_noise(self) -> ScenarioResult:
        """
        Scenario: Weak signal in high noise environment.
        
        Challenge: System must detect faint emitters in noisy conditions.
        """
        print("\n  📡 Testing Weak Signal in High Noise...")
        
        # Create sequence: weak signal with high noise
        configs = []
        for i in range(10):
            configs.append({
                "signal_type": "continuous",
                "custom_params": {
                    "strength": 0.15 + (i * 0.01),  # Very weak
                    "activity": 0.5
                }
            })
        
        results = self._run_sequence(configs, "high")
        
        success = results["detection_rate"] > 0.1  # Some detection is good
        return ScenarioResult(
            scenario_name="weak_signal_high_noise",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_rapidly_changing(self) -> ScenarioResult:
        """
        Scenario: Signal strength changes rapidly.
        
        Challenge: System must track dynamic emitters.
        """
        print("\n  📈 Testing Rapidly Changing Signal...")
        
        # Create sequence: varying strengths
        configs = []
        strengths = [0.2, 0.8, 0.3, 0.9, 0.1, 0.7, 0.4, 0.85, 0.15, 0.75]
        
        for strength in strengths:
            configs.append({
                "signal_type": "changing-strength",
                "custom_params": {
                    "strength": strength,
                    "strength_change": 0.0
                }
            })
        
        results = self._run_sequence(configs, "medium")
        
        success = results["detection_rate"] > 0.35
        return ScenarioResult(
            scenario_name="rapidly_changing",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_missing_observations(self) -> ScenarioResult:
        """
        Scenario: Some observations are missing (sensor failure).
        
        Challenge: System must handle incomplete data.
        """
        print("\n  ❓ Testing Missing Observations...")
        
        # Create sequence: some steps with missing data
        configs = []
        for i in range(10):
            configs.append({
                "signal_type": "continuous",
                "custom_params": {
                    "strength": 0.6,
                    # Simulate missing by having very low confidence
                    "activity": 0.5 if i % 3 != 0 else 0.0
                }
            })
        
        results = self._run_sequence(configs, "medium")
        
        success = results["detection_rate"] > 0.4
        return ScenarioResult(
            scenario_name="missing_observations",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_signal_type_change(self) -> ScenarioResult:
        """
        Scenario: Signal type changes over time.
        
        Challenge: System must adapt to changing emitter behavior.
        """
        print("\n  🔄 Testing Signal Type Change...")
        
        # Create sequence: different signal types
        configs = []
        types = ["continuous", "intermittent", "continuous", "changing-strength", 
                "noisy", "continuous", "disappearing", "continuous"]
        
        for signal_type in types:
            configs.append({
                "signal_type": signal_type,
                "custom_params": {"strength": 0.6}
            })
        
        results = self._run_sequence(configs, "medium")
        
        success = results["detection_rate"] > 0.4
        return ScenarioResult(
            scenario_name="signal_type_change",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=results["avg_reliability"],
            details=results
        )
    
    def scenario_multiple_regions(self) -> ScenarioResult:
        """
        Scenario: Multiple regions with different signal types.
        
        Challenge: System must track multiple emitters simultaneously.
        """
        print("\n  🌐 Testing Multiple Regions...")
        
        # Test different regions
        pipeline = SignalPipeline(noise_level="medium", seed=self.seed)
        
        region_configs = [
            {"region_id": "R1", "signal_type": "continuous", "custom_params": {"strength": 0.8}},
            {"region_id": "R2", "signal_type": "intermittent", "custom_params": {"strength": 0.6}},
            {"region_id": "R3", "signal_type": "appearing", "custom_params": {"strength": 0.7}},
            {"region_id": "R4", "signal_type": "disappearing", "custom_params": {"strength": 0.5}},
            {"region_id": "R5", "signal_type": "noisy", "custom_params": {"strength": 0.4}},
        ]
        
        outputs = []
        for config in region_configs:
            output = pipeline.process_region(
                region_id=config["region_id"],
                signal_type=config["signal_type"],
                custom_params=config.get("custom_params", {})
            )
            outputs.append(output)
        
        # Calculate statistics
        detections = [1 if out.observation.detected else 0 for out in outputs]
        confidences = [out.observation.confidence for out in outputs]
        uncertainties = [out.features.uncertainty for out in outputs]
        
        results = {
            "detection_rate": sum(detections) / len(detections) if detections else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "avg_uncertainty": sum(uncertainties) / len(uncertainties) if uncertainties else 0,
            "num_regions": len(outputs),
            "region_results": [(out.region_id, out.observation.detected) for out in outputs]
        }
        
        success = results["detection_rate"] > 0.4
        return ScenarioResult(
            scenario_name="multiple_regions",
            success=success,
            detection_rate=results["detection_rate"],
            avg_confidence=results["avg_confidence"],
            avg_uncertainty=results["avg_uncertainty"],
            avg_reliability=sum([out.features.reliability for out in outputs]) / len(outputs),
            details=results
        )
    
    def run_all_scenarios(self) -> List[ScenarioResult]:
        """Run all difficult scenarios."""
        print("\n" + "=" * 60)
        print("STEP 9: DIFFICULT SCENARIOS TESTING")
        print("=" * 60)
        
        scenarios = [
            self.scenario_intermittent_signal,
            self.scenario_sudden_appearance,
            self.scenario_weak_signal_high_noise,
            self.scenario_rapidly_changing,
            self.scenario_missing_observations,
            self.scenario_signal_type_change,
            self.scenario_multiple_regions,
        ]
        
        results = []
        for scenario_func in scenarios:
            try:
                result = scenario_func()
                results.append(result)
                print(f"    ✅ {result.scenario_name}: "
                      f"detection_rate={result.detection_rate:.2f}, "
                      f"success={result.success}")
            except Exception as e:
                print(f"    ❌ {scenario_func.__name__}: Error - {e}")
                results.append(ScenarioResult(
                    scenario_name=scenario_func.__name__,
                    success=False,
                    detection_rate=0.0,
                    avg_confidence=0.0,
                    avg_uncertainty=1.0,
                    avg_reliability=0.0,
                    details={"error": str(e)}
                ))
        
        return results
    
    def print_summary(self, results: List[ScenarioResult]):
        """Print a summary of scenario results."""
        print("\n" + "=" * 60)
        print("DIFFICULT SCENARIOS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r.success)
        total = len(results)
        
        print(f"\n  ✅ Passed: {passed}/{total}")
        print(f"  ❌ Failed: {total - passed}/{total}")
        print("\n  Detailed Results:")
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"    {status} - {result.scenario_name}:")
            print(f"        Detection Rate: {result.detection_rate:.2%}")
            print(f"        Avg Confidence: {result.avg_confidence:.3f}")
            print(f"        Avg Uncertainty: {result.avg_uncertainty:.3f}")
            print(f"        Avg Reliability: {result.avg_reliability:.3f}")
        
        return passed, total


if __name__ == "__main__":
    # Run difficult scenarios
    tester = DifficultScenarioTester(seed=42)
    results = tester.run_all_scenarios()
    passed, total = tester.print_summary(results)
    
    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 ALL DIFFICULT SCENARIOS PASSED!")
    else:
        print("⚠️ SOME SCENARIOS FAILED - Check details above")
    print("=" * 60)