"""TSRD Scenario - Realistic Dataset."""

from .scenarios import SCENARIO_CONFIGS

# Add S9 to the existing configs
SCENARIO_CONFIGS['S9'] = {
    'name': 'realistic_dataset',
    'num_emitters': 5,
    'persistence': 0.85,
    'intermittent': True,
    'noise_level': 'medium',
    'budget': 100,
    'description': 'Realistic TSRD-style emitters with frequency agility',
    'use_tsrd': True,
    'emitter_configs': [
        {
            'region_id': 'R7',
            'exists': True,
            'strength': 0.85,
            'activity': 0.9,
            'threat_relevance': 0.95,
            'bandwidth': 0.5,
            'is_intermittent': False,
            'persistence': 1.0,
            'frequency_agile': True,
            'hop_pattern': [1, 5, 9, 13, 17]
        },
        {
            'region_id': 'R3',
            'exists': True,
            'strength': 0.7,
            'activity': 0.8,
            'threat_relevance': 0.7,
            'bandwidth': 0.3,
            'is_intermittent': True,
            'persistence': 0.8,
            'frequency_agile': True,
            'hop_pattern': [2, 6, 10, 14, 18]
        },
        {
            'region_id': 'R12',
            'exists': True,
            'strength': 0.6,
            'activity': 0.7,
            'threat_relevance': 0.6,
            'bandwidth': 0.4,
            'is_intermittent': True,
            'persistence': 0.7,
            'frequency_agile': False
        }
    ]
}

print("✅ S9 scenario added!")
