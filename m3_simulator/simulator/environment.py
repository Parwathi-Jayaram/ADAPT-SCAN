"""Main environment for ADAPT-SCAN simulator."""

from typing import Dict, Tuple, Optional, Any
import random
from .ground_truth import GroundTruth
from .noise_model import NoiseModel
from .scanner import Scanner, ScanResult
from .scenarios import get_scenario_config


class Environment:
    """Main simulation environment."""
    
    def __init__(self, num_regions: int = 20, seed: int = 42):
        """Initialize the environment."""
        self.num_regions = num_regions
        self.seed = seed
        self.timestep = 0
        self.budget_remaining = 100.0
        self.budget_total = 100.0
        self.scan_cost = 1.0
        self.switching_cost = 0.5
        
        # Initialize components
        self.ground_truth = GroundTruth(num_regions, seed)
        self.noise_model = NoiseModel()
        self.scanner = Scanner(self.ground_truth, self.noise_model)
        
        # Track state
        self.current_region = None
        self.last_action = None
        self.observations = []
        self.scan_history = []
        self.done = False
        self.scenario_id = None
        self.current_config = None
        self.appearance_triggered = False
        self.using_real_data = False
        self.current_dataset = None
        self.tsrd_truth = None
    
    def reset(self, scenario: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """Reset environment to start of scenario."""
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        
        self.timestep = 0
        self.done = False
        self.current_region = None
        self.last_action = None
        self.observations = []
        self.scan_history = []
        self.appearance_triggered = False
        self.scenario_id = scenario
        
        # Load scenario configuration
        self.current_config = get_scenario_config(scenario)
        self.budget_total = self.current_config.get('budget', 100)
        self.budget_remaining = self.budget_total
        
        # Set noise level
        noise_level = self.current_config.get('noise_level', 'low')
        self.noise_model.set_noise_level(noise_level)
        
        # Initialize ground truth
        self.ground_truth.initialize_scenario(self.current_config)
        self.ground_truth.update(0)
        
        return self.get_observation_state()
    
    def step(self, action: str) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """Execute a scan action."""
        if self.done:
            return self.get_observation_state(), 0, True, {'error': 'Episode done'}
        
        # Check budget
        if self.budget_remaining < self.scan_cost:
            self.done = True
            return self.get_observation_state(), 0, True, {'reason': 'Budget exhausted'}
        
        # Apply switching cost
        actual_cost = self.scan_cost
        if self.current_region is not None and self.current_region != action:
            actual_cost += self.switching_cost
        
        if self.budget_remaining < actual_cost:
            self.done = True
            return self.get_observation_state(), 0, True, {'reason': 'Insufficient budget'}
        
        # Check for S7 sudden appearance
        self._check_sudden_appearance()
        
        # Update ground truth
        self.ground_truth.update(self.timestep + 1)
        
        # Consume budget
        self.budget_remaining -= actual_cost
        
        # Execute scan
        scan_seed = self.seed + self.timestep if self.seed else None
        result = self.scanner.scan(
            region_id=action,
            scan_cost=actual_cost,
            budget_remaining=self.budget_remaining,
            seed=scan_seed
        )
        
        self.current_region = action
        self.timestep += 1
        self.last_action = action
        
        if result:
            self.scan_history.append(result)
        
        observation = self.get_observation_state()
        
        if self.budget_remaining <= 0:
            self.done = True
        
        reward = self._calculate_reward(result)
        
        info = {
            'scan_result': result.__dict__ if result else None,
            'timestep': self.timestep,
            'budget_remaining': self.budget_remaining,
            'cost': actual_cost,
            'action': action
        }
        
        return observation, reward, self.done, info
    
    def _check_sudden_appearance(self) -> None:
        """Check if sudden appearance should trigger (for S7)."""
        if self.scenario_id != 'S7' or self.appearance_triggered:
            return
        
        appearance = self.current_config.get('sudden_appearance')
        if appearance and self.timestep == appearance.get('time', 10):
            region = appearance.get('region', 'R15')
            
            from .emitter import Emitter
            emitter = Emitter(
                region_id=region,
                exists=True,
                strength=appearance.get('strength', 0.9),
                activity=0.9,
                threat_relevance=appearance.get('threat', 0.95),
                bandwidth=appearance.get('bandwidth', 0.5),
                is_intermittent=False,
                persistence=1.0
            )
            
            if region not in self.ground_truth.emitters:
                self.ground_truth.emitters[region] = []
            self.ground_truth.emitters[region].append(emitter)
            self.appearance_triggered = True
    
    def _calculate_reward(self, scan_result: Optional[ScanResult]) -> float:
        """Calculate reward based on information gain and cost."""
        if scan_result is None:
            return 0.0
        
        reward = 0.0
        if scan_result.detected:
            reward += scan_result.confidence * 0.5
            truth = self.ground_truth.get_region_truth(scan_result.region_id)
            if truth.get('exists', False):
                reward += truth.get('threat_relevance', 0) * 0.3
        
        if scan_result.is_false_alarm:
            reward -= 0.2
        
        reward -= scan_result.scan_cost * 0.1
        
        return max(-1.0, min(1.0, reward))
    
    def get_observation_state(self) -> Dict[str, Any]:
        """Return what the AI sees (partial observability)."""
        hidden = self.ground_truth.get_hidden_state()
        
        regions = []
        for i in range(1, self.num_regions + 1):
            region_id = f'R{i}'
            truth = hidden.get(region_id, {})
            
            last_scan = None
            for scan in reversed(self.scan_history):
                if scan.region_id == region_id:
                    last_scan = scan
                    break
            
            if last_scan:
                regions.append({
                    'region_id': region_id,
                    'existence': float(last_scan.detected),
                    'uncertainty': 1.0 - last_scan.confidence,
                    'threat_relevance': truth.get('threat_relevance', 0),
                    'last_observed': last_scan.timestamp,
                    'status': 'scanned',
                    'detected': last_scan.detected,
                    'strength': last_scan.strength,
                    'snr': last_scan.snr,
                    'confidence': last_scan.confidence
                })
            else:
                regions.append({
                    'region_id': region_id,
                    'existence': 0.0,
                    'uncertainty': 0.9,
                    'threat_relevance': 0.0,
                    'last_observed': None,
                    'status': 'unknown',
                    'detected': None,
                    'strength': None,
                    'snr': None,
                    'confidence': None
                })
        
        detected_count = sum(1 for r in regions if r.get('detected', False))
        high_priority_count = sum(1 for r in regions if r.get('threat_relevance', 0) > 0.7)
        uncertainty_hotspots = sum(1 for r in regions if r.get('uncertainty', 0) > 0.7)
        
        return {
            'regions': regions,
            'timestep': self.timestep,
            'budget_remaining': self.budget_remaining,
            'budget_total': self.budget_total,
            'budget_remaining_frac': self.budget_remaining / self.budget_total if self.budget_total > 0 else 0,
            'current_scan': self.current_region,
            'scenario': self.scenario_id,
            'intelligence': {
                'detected_count': detected_count,
                'high_priority_count': high_priority_count,
                'uncertainty_hotspots': uncertainty_hotspots
            }
        }
    
    def get_ground_truth(self) -> Dict[str, Any]:
        """For testing only - get hidden ground truth."""
        return self.ground_truth.get_hidden_state()
    
    def get_budget(self) -> float:
        """Get remaining budget."""
        return self.budget_remaining
    
    def is_done(self) -> bool:
        """Check if episode is complete."""
        return self.done
