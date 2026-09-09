"""Noise model for ADAPT-SCAN simulator."""

import random
import numpy as np
from typing import Dict, Any


class NoiseModel:
    """Applies noise to ground truth to create observations."""
    
    def __init__(self):
        self.current_noise_level = 'low'
        self.noise_params = {
            'low': {
                'snr_range': (10, 20),
                'miss_prob': 0.05,
                'false_alert': 0.02,
                'strength_noise': 0.05,
                'confidence_factor': 0.9
            },
            'medium': {
                'snr_range': (5, 10),
                'miss_prob': 0.15,
                'false_alert': 0.08,
                'strength_noise': 0.12,
                'confidence_factor': 0.7
            },
            'high': {
                'snr_range': (2, 5),
                'miss_prob': 0.30,
                'false_alert': 0.15,
                'strength_noise': 0.20,
                'confidence_factor': 0.5
            },
            'very_high': {
                'snr_range': (0, 2),
                'miss_prob': 0.50,
                'false_alert': 0.30,
                'strength_noise': 0.30,
                'confidence_factor': 0.3
            }
        }
    
    def set_noise_level(self, level: str) -> None:
        """Set the current noise level."""
        if level in self.noise_params:
            self.current_noise_level = level
        else:
            raise ValueError(f"Unknown noise level: {level}")
    
    def apply_noise(self, truth: Dict[str, Any], region_id: str, 
                    seed: int = None) -> Dict[str, Any]:
        """
        Apply noise to ground truth to create an observation.
        
        Args:
            truth: Ground truth dictionary for the region
            region_id: Region being observed
            seed: Random seed for reproducibility
            
        Returns:
            Dict with noisy observation
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        params = self.noise_params[self.current_noise_level]
        
        # Check if region exists in truth
        exists_in_truth = truth.get('exists', False)
        
        # Determine if we detect it (miss probability)
        detected = False
        if exists_in_truth:
            detected = random.random() > params['miss_prob']
        
        # False alarm for empty regions
        if not exists_in_truth:
            detected = random.random() < params['false_alert']
        
        if not detected and exists_in_truth:
            # Missed detection - return empty observation
            return {
                'region_id': region_id,
                'detected': False,
                'strength': 0.0,
                'bandwidth': 0.0,
                'snr': 0.0,
                'confidence': 0.0,
                'noise_level': self.current_noise_level,
                'is_false_alarm': False
            }
        
        if not detected and not exists_in_truth:
            # True negative
            return {
                'region_id': region_id,
                'detected': False,
                'strength': 0.0,
                'bandwidth': 0.0,
                'snr': 0.0,
                'confidence': 0.0,
                'noise_level': self.current_noise_level,
                'is_false_alarm': False
            }
        
        # True positive or false alarm
        if exists_in_truth:
            # True positive - add noise to measurements
            true_strength = truth.get('strength', 0.0)
            true_bandwidth = truth.get('bandwidth', 0.3)
            
            # Add Gaussian noise to strength
            noise_std = params['strength_noise']
            strength_noise = np.random.normal(0, noise_std)
            observed_strength = max(0.0, min(1.0, true_strength + strength_noise))
            
            # Add noise to bandwidth
            bandwidth_noise = np.random.normal(0, 0.05)
            observed_bandwidth = max(0.0, min(1.0, true_bandwidth + bandwidth_noise))
            
            # Calculate SNR
            snr = random.uniform(*params['snr_range'])
            
            # Calculate confidence based on SNR
            confidence = min(1.0, (snr / 20) * params['confidence_factor'])
            
            return {
                'region_id': region_id,
                'detected': True,
                'strength': observed_strength,
                'bandwidth': observed_bandwidth,
                'snr': snr,
                'confidence': confidence,
                'noise_level': self.current_noise_level,
                'is_false_alarm': False
            }
        else:
            # False alarm - generate fake signal
            fake_strength = random.uniform(0.1, 0.4)
            fake_bandwidth = random.uniform(0.1, 0.3)
            
            return {
                'region_id': region_id,
                'detected': True,
                'strength': fake_strength,
                'bandwidth': fake_bandwidth,
                'snr': random.uniform(0, 3),
                'confidence': random.uniform(0, 0.3),
                'noise_level': self.current_noise_level,
                'is_false_alarm': True
            }
