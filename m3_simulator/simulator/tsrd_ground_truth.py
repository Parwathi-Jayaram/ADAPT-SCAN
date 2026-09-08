"""
TSRD Ground Truth Adapter
Uses real datasets as ground truth source
"""

import random
from typing import Dict, List, Any


class TSRDGroundTruth:
    """Ground truth using TSRD and other datasets."""
    
    def __init__(self, dataset_loader, num_regions=20, seed=42):
        self.loader = dataset_loader
        self.num_regions = num_regions
        self.seed = seed
        self.emitters = {}
        self.timestep = 0
        self.dataset_name = 'TSRD_Stare'
        
        # Load all datasets
        self.datasets = self.loader.load_all_datasets()
        self.switch_dataset('TSRD_Stare')
    
    def switch_dataset(self, dataset_name: str):
        """Switch to a different dataset."""
        if dataset_name in self.datasets:
            self.dataset_name = dataset_name
            self.emitters = self.datasets[dataset_name].copy()
            print(f"✅ Switched to dataset: {dataset_name}")
        else:
            print(f"⚠️ Dataset {dataset_name} not found. Available: {list(self.datasets.keys())}")
    
    def list_datasets(self):
        """List all available datasets."""
        return list(self.datasets.keys())
    
    def get_hidden_state(self) -> Dict[str, Dict[str, Any]]:
        """Get hidden ground truth for all regions."""
        state = {}
        for i in range(1, self.num_regions + 1):
            region_id = f'R{i}'
            state[region_id] = self.get_region_truth(region_id)
        return state
    
    def get_region_truth(self, region_id: str) -> Dict[str, Any]:
        """Get ground truth for a specific region."""
        # Check if any emitter is in this region
        for em_id, emitter in self.emitters.items():
            if emitter.get('region_id') == region_id and emitter.get('exists', False):
                return {
                    'exists': True,
                    'strength': emitter.get('strength', 0.5),
                    'activity': emitter.get('activity', 0.7),
                    'threat_relevance': emitter.get('threat_relevance', 0.5),
                    'bandwidth': emitter.get('bandwidth', 0.3),
                    'is_intermittent': emitter.get('is_intermittent', False),
                    'emitter_count': 1,
                    'data_source': emitter.get('data_source', 'unknown'),
                    'emitter_id': em_id
                }
        
        return {
            'exists': False,
            'strength': 0.0,
            'activity': 0.0,
            'threat_relevance': 0.0,
            'bandwidth': 0.0,
            'is_intermittent': False,
            'emitter_count': 0
        }
    
    def update(self, timestep: int):
        """Update emitters over time."""
        self.timestep = timestep
        
        for em_id, emitter in self.emitters.items():
            # Random intermittency
            if emitter.get('is_intermittent', False):
                if random.random() > emitter.get('persistence', 0.8):
                    emitter['exists'] = not emitter.get('exists', True)
            
            # Frequency agility
            if emitter.get('frequency_agile', False) and emitter.get('exists', False):
                hop = emitter.get('hop_pattern', [1, 5, 9, 13, 17])
                current = emitter.get('current_hop', 0)
                emitter['current_hop'] = (current + 1) % len(hop)
                new_region = f"R{hop[emitter['current_hop']]}"
                emitter['region_id'] = new_region
            
            # Random strength variation
            if emitter.get('exists', False):
                emitter['strength'] = max(0.1, min(1.0, 
                    emitter['strength'] + random.uniform(-0.05, 0.05)))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current dataset."""
        total = len(self.emitters)
        active = sum(1 for e in self.emitters.values() if e.get('exists', False))
        agile = sum(1 for e in self.emitters.values() if e.get('frequency_agile', False))
        
        return {
            'dataset': self.dataset_name,
            'total_emitters': total,
            'active_emitters': active,
            'frequency_agile': agile,
            'avg_strength': sum(e.get('strength', 0) for e in self.emitters.values()) / max(1, total)
        }
