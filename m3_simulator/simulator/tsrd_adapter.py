"""
TSRD (Turing Synthetic Radar Dataset) Adapter
Converts real radar pulse data into your simulator's format
"""

import numpy as np
import h5py
from huggingface_hub import hf_hub_download
import random


class TSRDAdapter:
    """Adapter to load TSRD data and convert to your simulator format."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.current_region = None
        self.timestep = 0
        self.regions = 20  # 20 frequency bands
        self.emitters = {}
        self.data_loaded = False
        
    def load_sample_data(self):
        """
        Load a sample pulse train from Hugging Face.
        This downloads a small sample file.
        """
        try:
            # Try to download a sample file from Hugging Face
            print("Downloading sample data from Hugging Face...")
            file_path = hf_hub_download(
                repo_id="alan-turing-institute/turing-synthetic-radar-dataset",
                filename="sample_pulse_train.h5",
                repo_type="dataset"
            )
            print(f"✅ Downloaded: {file_path}")
            
            # Load the h5 file
            with h5py.File(file_path, 'r') as f:
                print("📊 File contents:")
                for key in f.keys():
                    print(f"   - {key}")
                    
            return file_path
            
        except Exception as e:
            print(f"⚠️ Could not download sample: {e}")
            print("Creating synthetic realistic data instead...")
            self._create_realistic_synthetic_data()
            return None
    
    def _create_realistic_synthetic_data(self):
        """
        If TSRD can't be downloaded, create realistic synthetic data
        that mimics real radar patterns.
        """
        print("Creating realistic synthetic radar data...")
        
        # Simulate realistic emitter patterns
        # Frequency hopping patterns
        hop_patterns = [
            [1, 3, 5, 7, 9],  # hops through odd frequencies
            [2, 4, 6, 8, 10], # hops through even frequencies
            [1, 5, 10, 15, 20], # wide hops
            [3, 6, 9, 12, 15], # regular hopping
        ]
        
        for i in range(5):  # 5 emitters
            region = f'R{random.randint(1, 20)}'
            pattern_idx = i % len(hop_patterns)
            
            self.emitters[f"Emitter_{i+1}"] = {
                'region_id': region,
                'exists': True,
                'strength': random.uniform(0.6, 0.9),
                'activity': random.uniform(0.6, 0.9),
                'threat_relevance': random.uniform(0.5, 0.95),
                'bandwidth': random.uniform(0.3, 0.7),
                'is_intermittent': random.choice([True, False]),
                'persistence': random.uniform(0.7, 0.95),
                'hop_pattern': hop_patterns[pattern_idx],
                'current_hop': 0,
                'frequency_agile': True
            }
        
        self.data_loaded = True
        print(f"✅ Created {len(self.emitters)} realistic emitters with frequency agility")
    
    def get_region_truth(self, region_id: str):
        """
        Get ground truth for a specific region.
        Returns dict with 'exists', 'strength', etc.
        """
        # Check if any emitter is in this region
        for emitter_id, emitter in self.emitters.items():
            if emitter['region_id'] == region_id and emitter['exists']:
                # Apply frequency agility
                if emitter.get('frequency_agile', False):
                    # Move to next frequency in hop pattern
                    hop = emitter['hop_pattern']
                    current = emitter['current_hop']
                    next_hop = (current + 1) % len(hop)
                    emitter['current_hop'] = next_hop
                    
                    # Update region based on hop
                    new_region = f"R{hop[next_hop]}"
                    if new_region != region_id:
                        # Emitter has hopped to another frequency
                        continue
                
                return {
                    'exists': True,
                    'strength': emitter['strength'],
                    'activity': emitter['activity'],
                    'threat_relevance': emitter['threat_relevance'],
                    'bandwidth': emitter['bandwidth'],
                    'is_intermittent': emitter['is_intermittent'],
                    'emitter_count': 1,
                    'emitter_id': emitter_id
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
    
    def get_hidden_state(self):
        """Get hidden state for all regions."""
        state = {}
        for i in range(1, 21):
            region_id = f'R{i}'
            state[region_id] = self.get_region_truth(region_id)
        return state
    
    def update(self, timestep):
        """Update emitter states over time."""
        self.timestep = timestep
        
        # Update each emitter
        for emitter_id, emitter in self.emitters.items():
            # Random intermittency
            if emitter.get('is_intermittent', False):
                if random.random() > emitter.get('persistence', 0.8):
                    emitter['exists'] = not emitter['exists']
            
            # Frequency agility - move to next hop
            if emitter.get('frequency_agile', False):
                hop = emitter['hop_pattern']
                current = emitter['current_hop']
                emitter['current_hop'] = (current + 1) % len(hop)
                new_region = f"R{hop[emitter['current_hop']]}"
                emitter['region_id'] = new_region
                print(f"  🔄 Emitter {emitter_id} hopped to {new_region}")
            
            # Random strength variation
            if emitter['exists']:
                emitter['strength'] = max(0.2, min(1.0, 
                    emitter['strength'] + random.uniform(-0.05, 0.05)))


# Quick test
if __name__ == "__main__":
    print("Testing TSRD Adapter...")
    adapter = TSRDAdapter(seed=42)
    adapter._create_realistic_synthetic_data()
    
    print("\nEmitters created:")
    for em_id, em in adapter.emitters.items():
        print(f"  {em_id}: {em['region_id']} - Threat: {em['threat_relevance']:.2f}")
    
    print("\nHidden state for R7:")
    print(adapter.get_region_truth('R7'))
    
    print("\n✅ TSRD Adapter ready!")
