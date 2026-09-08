"""Emitter lifecycle module for ADAPT-SCAN simulator."""

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class Emitter:
    """Represents a signal emitter in the spectrum."""
    
    region_id: str
    exists: bool = True
    strength: float = 0.7
    activity: float = 0.8
    threat_relevance: float = 0.5
    bandwidth: float = 0.3
    is_intermittent: bool = False
    persistence: float = 0.9
    appearance_time: int = 0
    disappearance_time: Optional[int] = None
    
    def update(self, timestep: int, random_seed: Optional[int] = None) -> None:
        """
        Update emitter state based on lifecycle rules.
        
        Args:
            timestep: Current simulation timestep
            random_seed: Optional seed for reproducibility
        """
        if random_seed is not None:
            random.seed(random_seed + timestep)
        
        # Check for disappearance
        if self.disappearance_time is not None and timestep >= self.disappearance_time:
            self.exists = False
            return
        
        # Handle intermittency
        if self.is_intermittent:
            # Toggle on/off based on activity probability
            self.exists = random.random() < self.activity
        
        # Gradual strength changes (small random walk)
        if self.exists:
            self.strength = max(0.0, min(1.0, 
                                         self.strength + random.uniform(-0.03, 0.03)))
            self.activity = max(0.0, min(1.0, 
                                        self.activity + random.uniform(-0.02, 0.02)))
