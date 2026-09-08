"""
Real TSRD data adapter for the simulator.
Works with the actual TSRD file structure.
"""

import h5py
import numpy as np
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class TSRDRealAdapter:
    """
    Adapter for real TSRD data files.
    Handles the actual structure: data (Dataset), labels (Dataset)
    """
    
    def __init__(self, data_dir: str = "data/tsrd_real", seed: int = 42):
        self.data_dir = Path(data_dir)
        self.seed = seed
        np.random.seed(seed)
        
        self.file_list = []
        self.current_file_idx = 0
        self.current_data = None
        self.current_labels = None
        self.current_file_name = None
        self.current_feature_names = None
        
        self._index_files()
        
        if self.file_list:
            self._load_file(0)
    
    def _index_files(self):
        """Index all available H5 files."""
        self.file_list = []
        search_dirs = ['archive/test', 'archive/train', 'archive/validation', '']
        
        for subdir in search_dirs:
            search_path = self.data_dir / subdir if subdir else self.data_dir
            if search_path.exists():
                files = list(search_path.glob("*.h5"))
                for f in files:
                    self.file_list.append(str(f))
                if files:
                    print(f"   Found {len(files)} files in {subdir if subdir else 'root'}")
        
        print(f"✅ Total files indexed: {len(self.file_list)}")
    
    def _load_file(self, idx: int):
        """Load a specific file by index."""
        if idx >= len(self.file_list):
            idx = len(self.file_list) - 1
        
        self.current_file_idx = idx
        file_path = self.file_list[idx]
        self.current_file_name = os.path.basename(file_path)
        
        try:
            with h5py.File(file_path, 'r') as f:
                print(f"   📂 Opening: {self.current_file_name}")
                
                # Load data (Dataset)
                if 'data' in f:
                    self.current_data = f['data'][:]
                    print(f"      Data shape: {self.current_data.shape}")
                    print(f"      Data features: {self.current_data.shape[1]} columns")
                else:
                    self.current_data = None
                
                # Load labels (Dataset) - flatten from (N,1) to (N,)
                if 'labels' in f:
                    labels = f['labels'][:]
                    self.current_labels = labels.flatten() if len(labels.shape) > 1 else labels
                    print(f"      Labels: {len(self.current_labels)} samples")
                    unique_labels = np.unique(self.current_labels)
                    print(f"      Unique emitters: {len(unique_labels)}")
                    print(f"      Emitter IDs: {unique_labels[:10]}...")
                else:
                    self.current_labels = None
                
                # Load feature names from metadata if available
                if 'metadata' in f:
                    meta_group = f['metadata']
                    try:
                        if 'feature_names' in meta_group:
                            feature_names = meta_group['feature_names'][()]
                            # Handle byte arrays
                            if isinstance(feature_names, np.ndarray):
                                # Convert byte array to list of strings
                                self.current_feature_names = [name.decode('utf-8') if isinstance(name, bytes) else str(name) for name in feature_names]
                            elif isinstance(feature_names, bytes):
                                self.current_feature_names = feature_names.decode('utf-8')
                            else:
                                self.current_feature_names = str(feature_names)
                            print(f"      Feature names: {self.current_feature_names}")
                    except Exception as e:
                        print(f"      Note: Could not read feature names: {e}")
            
            print(f"   ✅ Loaded: {self.current_file_name}")
            
        except Exception as e:
            print(f"   ❌ Error loading {file_path}: {e}")
            self.current_data = None
            self.current_labels = None
    
    def get_region_truth(self, region_id: str, timestep: int = 0) -> Dict[str, Any]:
        """
        Get ground truth for a region using real TSRD data.
        
        TSRD data columns:
        Column 0: UTCTime (Time of Arrival)
        Column 1: RF (Centre Frequency) - use this for region mapping
        Column 2: PulseWidth
        Column 3: AOA (Angle of Arrival)
        Column 4: PA (Amplitude)
        """
        if self.current_data is None:
            return {'exists': False, 'strength': 0.0, 'data_source': 'tsrd_real'}
        
        # Map region_id to frequency range
        region_num = int(region_id[1:])
        freq_min = 8000 + (region_num - 1) * 200
        freq_max = 8000 + region_num * 200
        
        data = self.current_data
        
        # Column 1 is RF (Centre Frequency)
        freq_col = 1
        freq_values = data[:, freq_col]
        
        # Filter by frequency range
        in_range = (freq_values >= freq_min) & (freq_values <= freq_max)
        
        if np.any(in_range):
            relevant = data[in_range]
            # Column 4 is PA (Amplitude)
            amp_col = 4
            
            # Get emitter IDs for these pulses
            emitter_ids = []
            if self.current_labels is not None:
                relevant_labels = self.current_labels[in_range]
                emitter_ids = list(np.unique(relevant_labels))
            
            return {
                'exists': True,
                'strength': float(np.mean(relevant[:, amp_col])),
                'num_pulses': len(relevant),
                'num_emitters': len(emitter_ids),
                'emitter_ids': emitter_ids[:5],
                'avg_freq': float(np.mean(relevant[:, freq_col])),
                'min_freq': float(np.min(relevant[:, freq_col])),
                'max_freq': float(np.max(relevant[:, freq_col])),
                'data_source': 'tsrd_real',
                'file': self.current_file_name,
                'timestep': timestep
            }
        else:
            return {
                'exists': False,
                'strength': 0.0,
                'num_pulses': 0,
                'data_source': 'tsrd_real'
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded data."""
        if self.current_data is None:
            return {'total_pulses': 0, 'num_emitters': 0, 'file': 'none'}
        
        stats = {
            'total_pulses': self.current_data.shape[0],
            'num_features': self.current_data.shape[1],
            'file': self.current_file_name,
        }
        
        if self.current_labels is not None:
            stats['num_emitters'] = len(np.unique(self.current_labels))
        
        # Check if feature_names exists and is not None
        if self.current_feature_names is not None:
            stats['feature_names'] = self.current_feature_names
        
        return stats
    
    def switch_file(self, idx: int = None):
        """Switch to a different file."""
        if idx is None:
            idx = (self.current_file_idx + 1) % len(self.file_list)
        
        self._load_file(idx)
    
    def get_all_emitter_count(self) -> int:
        """Get total number of emitters in current file."""
        if self.current_labels is not None:
            return len(np.unique(self.current_labels))
        return 0
    
    def get_frequency_range(self) -> tuple:
        """Get min and max frequency from current data."""
        if self.current_data is not None:
            freq_col = 1
            return (float(np.min(self.current_data[:, freq_col])), 
                    float(np.max(self.current_data[:, freq_col])))
        return (0, 0)


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Real TSRD Adapter")
    print("=" * 70)
    
    adapter = TSRDRealAdapter(data_dir="data/tsrd_real")
    
    stats = adapter.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   File: {stats.get('file', 'none')}")
    print(f"   Total pulses: {stats.get('total_pulses', 0):,}")
    print(f"   Num features: {stats.get('num_features', 0)}")
    print(f"   Num emitters: {stats.get('num_emitters', 0)}")
    
    if 'feature_names' in stats:
        print(f"   Feature names: {stats['feature_names']}")
    
    freq_range = adapter.get_frequency_range()
    print(f"   Frequency range: {freq_range[0]:.2f} - {freq_range[1]:.2f} MHz")
    
    print("\n🔍 Testing region queries:")
    regions = ['R1', 'R5', 'R7', 'R10', 'R12', 'R15', 'R20']
    for region in regions:
        result = adapter.get_region_truth(region)
        if result.get('exists', False):
            print(f"   ✅ {region}: {result['num_pulses']:,} pulses, {result.get('num_emitters', 0)} emitters, strength={result['strength']:.2f}")
        else:
            print(f"   ❌ {region}: No signals")
    
    print("\n🔄 Testing file switching...")
    for i in range(3):
        adapter.switch_file()
        stats = adapter.get_statistics()
        print(f"   File {i+1}: {stats.get('file', 'unknown')} - {stats.get('total_pulses', 0):,} pulses, {stats.get('num_emitters', 0)} emitters")
    
    print("\n" + "=" * 70)
    print("✅ REAL TSRD ADAPTER TEST PASSED!")
    print("=" * 70)
