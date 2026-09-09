"""Scenarios for ADAPT-SCAN simulator."""

import json
from typing import Dict, Any
import os

# Define scenarios
SCENARIO_CONFIGS = {
    'S1': {
        'name': 'low_complexity',
        'num_emitters': 1,
        'persistence': 1.0,
        'intermittent': False,
        'noise_level': 'low',
        'budget': 100,
        'description': 'One persistent emitter in fixed location',
        'emitter_configs': [
            {
                'region_id': 'R7',
                'exists': True,
                'strength': 0.8,
                'activity': 0.9,
                'threat_relevance': 0.9,
                'bandwidth': 0.4,
                'is_intermittent': False,
                'persistence': 1.0
            }
        ]
    },
    'S2': {
        'name': 'medium_complexity',
        'num_emitters': 3,
        'persistence': 0.9,
        'intermittent': True,
        'noise_level': 'medium',
        'budget': 100,
        'description': 'Three emitters with some intermittency'
    },
    'S3': {
        'name': 'intermittent',
        'num_emitters': 2,
        'persistence': 0.6,
        'intermittent': True,
        'noise_level': 'low',
        'budget': 100,
        'description': 'Emitters turning on and off'
    },
    'S4': {
        'name': 'dynamic',
        'num_emitters': 4,
        'persistence': 0.7,
        'intermittent': True,
        'noise_level': 'medium',
        'budget': 100,
        'description': 'Emitters moving/changing behavior'
    },
    'S5': {
        'name': 'high_uncertainty',
        'num_emitters': 2,
        'persistence': 0.5,
        'intermittent': True,
        'noise_level': 'high',
        'budget': 80,
        'description': 'Poor detection conditions'
    },
    'S6': {
        'name': 'low_budget',
        'num_emitters': 3,
        'persistence': 0.8,
        'intermittent': False,
        'noise_level': 'low',
        'budget': 30,
        'description': 'Very limited scanning resources'
    },
    'S7': {
        'name': 'sudden_important',
        'num_emitters': 1,
        'persistence': 0.95,
        'intermittent': False,
        'noise_level': 'low',
        'budget': 100,
        'description': 'High-priority emitter suddenly appears',
        'sudden_appearance': {
            'time': 10,
            'region': 'R15',
            'threat': 0.95,
            'strength': 0.9,
            'bandwidth': 0.5
        }
    },
    'S8': {
        'name': 'high_noise',
        'num_emitters': 5,
        'persistence': 0.8,
        'intermittent': True,
        'noise_level': 'very_high',
        'budget': 100,
        'description': 'Many noisy emitters, hard to distinguish'
    }
}


def get_scenario_config(scenario_id: str) -> Dict[str, Any]:
    """Get configuration for a scenario."""
    config = SCENARIO_CONFIGS.get(scenario_id)
    if config is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    return config.copy()


def list_scenarios() -> list:
    """List all available scenario IDs."""
    return list(SCENARIO_CONFIGS.keys())


def load_scenarios_from_file(filepath: str = None) -> Dict[str, Any]:
    """Load scenarios from a JSON file (optional)."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), '..', 'configs', 'scenario_configs.json')
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    
    return SCENARIO_CONFIGS
