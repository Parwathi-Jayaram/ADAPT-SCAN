"""Scanner module for ADAPT-SCAN simulator."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import random
from .ground_truth import GroundTruth
from .noise_model import NoiseModel


@dataclass
class ScanResult:
    """Result of a scan action."""
    region_id: str
    detected: bool
    strength: float
    bandwidth: float
    snr: float
    confidence: float
    is_false_alarm: bool
    noise_level: str
    timestamp: int
    scan_cost: float


class Scanner:
    """Executes scans and returns observations."""
    
    def __init__(self, ground_truth: GroundTruth, noise_model: NoiseModel):
        self.ground_truth = ground_truth
        self.noise_model = noise_model
        self.scan_history: list = []
        self.timestamp = 0
    
    def scan(self, region_id: str, scan_cost: float = 1.0,
             budget_remaining: float = 100.0, seed: int = None) -> Optional[ScanResult]:
        """
        Execute a scan on a region.
        
        Args:
            region_id: Region to scan (e.g., 'R7')
            scan_cost: Cost of this scan
            budget_remaining: Remaining budget
            seed: Random seed for reproducibility
            
        Returns:
            ScanResult if budget allows, None otherwise
        """
        if budget_remaining < scan_cost:
            return None
        
        # Get ground truth for this region
        truth = self.ground_truth.get_region_truth(region_id)
        
        # Apply noise
        observation = self.noise_model.apply_noise(
            truth=truth,
            region_id=region_id,
            seed=seed
        )
        
        # Create scan result
        result = ScanResult(
            region_id=region_id,
            detected=observation.get('detected', False),
            strength=observation.get('strength', 0.0),
            bandwidth=observation.get('bandwidth', 0.0),
            snr=observation.get('snr', 0.0),
            confidence=observation.get('confidence', 0.0),
            is_false_alarm=observation.get('is_false_alarm', False),
            noise_level=observation.get('noise_level', 'low'),
            timestamp=self.timestamp,
            scan_cost=scan_cost
        )
        
        self.scan_history.append(result)
        self.timestamp += 1
        
        return result
    
    def get_last_scan(self) -> Optional[ScanResult]:
        """Get the most recent scan result."""
        if self.scan_history:
            return self.scan_history[-1]
        return None
    
    def get_scan_history(self) -> list:
        """Get all scan results."""
        return self.scan_history.copy()
