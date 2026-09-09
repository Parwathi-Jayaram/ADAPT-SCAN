"""Hidden ground truth state - AI never sees this directly."""

from typing import Dict, List, Optional, Any
import random
from .emitter import Emitter


class GroundTruth:
    """Hidden ground truth state - AI never sees this directly."""
    
    def __init__(self, num_regions: int = 20, seed: int = 42):
        self.num_regions = num_regions
        self.seed = seed
        self.timestep = 0
        self.emitters: Dict[str, List[Emitter]] = {}
        random.seed(seed)
        
    def initialize_scenario(self, scenario_config: dict) -> None:
        """
        Set up emitters based on scenario configuration.
        
        Args:
            scenario_config: Configuration dictionary from scenarios.py
        """
        self.timestep = 0
        self.emitters = {}
        
        # Get emitter configs from scenario
        emitter_configs = scenario_config.get('emitter_configs', [])
        num_emitters = scenario_config.get('num_emitters', 1)
        
        # If specific configs provided, use them
        if emitter_configs:
            for config in emitter_configs:
                emitter = Emitter(
                    region_id=config.get('region_id', f'R{random.randint(1, self.num_regions)}'),
                    exists=config.get('exists', True),
                    strength=config.get('strength', 0.7),
                    activity=config.get('activity', 0.8),
                    threat_relevance=config.get('threat_relevance', 0.5),
                    bandwidth=config.get('bandwidth', 0.3),
                    is_intermittent=config.get('is_intermittent', False),
                    persistence=config.get('persistence', 0.9)
                )
                if emitter.region_id not in self.emitters:
                    self.emitters[emitter.region_id] = []
                self.emitters[emitter.region_id].append(emitter)
        else:
            # Auto-generate emitters
            self._generate_random_emitters(num_emitters, scenario_config)
    
    def _generate_random_emitters(self, num_emitters: int, config: dict) -> None:
        """Generate random emitters based on config."""
        for i in range(num_emitters):
            region_id = f'R{random.randint(1, self.num_regions)}'
            
            # Ensure at least one high-threat emitter
            threat = random.uniform(0.3, 0.8)
            if i == 0:  # First emitter is more important
                threat = random.uniform(0.7, 0.95)
            
            emitter = Emitter(
                region_id=region_id,
                exists=True,
                strength=random.uniform(0.4, 0.9),
                activity=random.uniform(0.5, 0.9),
                threat_relevance=threat,
                bandwidth=random.uniform(0.1, 0.5),
                is_intermittent=config.get('intermittent', False),
                persistence=config.get('persistence', 0.9)
            )
            
            if region_id not in self.emitters:
                self.emitters[region_id] = []
            self.emitters[region_id].append(emitter)
    
    def update(self, timestep: int) -> None:
        """
        Update all emitters based on lifecycle rules.
        
        Args:
            timestep: Current simulation timestep
        """
        self.timestep = timestep
        
        for region_id, emitters in self.emitters.items():
            for emitter in emitters:
                emitter.update(timestep, self.seed + timestep)
    
    def get_hidden_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the complete hidden ground truth.
        
        Returns:
            Dict with region_id as key and hidden state as value
        """
        state = {}
        for region_id, emitters in self.emitters.items():
            active_emitters = [e for e in emitters if e.exists]
            
            if active_emitters:
                state[region_id] = {
                    'exists': True,
                    'strength': max(e.strength for e in active_emitters),
                    'activity': max(e.activity for e in active_emitters),
                    'threat_relevance': max(e.threat_relevance for e in active_emitters),
                    'bandwidth': max(e.bandwidth for e in active_emitters),
                    'emitter_count': len(active_emitters),
                    'is_intermittent': any(e.is_intermittent for e in active_emitters)
                }
            else:
                state[region_id] = {
                    'exists': False,
                    'strength': 0.0,
                    'activity': 0.0,
                    'threat_relevance': 0.0,
                    'bandwidth': 0.0,
                    'emitter_count': 0,
                    'is_intermittent': False
                }
        
        return state
    
    def get_region_truth(self, region_id: str) -> Dict[str, Any]:
        """
        Get ground truth for a specific region.
        
        Args:
            region_id: Region to query (e.g., 'R7')
            
        Returns:
            Dict with hidden truth for that region
        """
        hidden = self.get_hidden_state()
        return hidden.get(region_id, {
            'exists': False,
            'strength': 0.0,
            'activity': 0.0,
            'threat_relevance': 0.0,
            'bandwidth': 0.0,
            'emitter_count': 0
        })
