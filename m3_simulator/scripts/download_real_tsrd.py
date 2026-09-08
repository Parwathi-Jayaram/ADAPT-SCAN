"""
Download real TSRD files using correct file structure.
"""

import os
import json
import h5py
import numpy as np
from huggingface_hub import hf_hub_download, list_repo_files


def list_available_files():
    """List all available files in the repository."""
    print("📂 Listing available files...")
    files = list_repo_files(
        repo_id="alan-turing-institute/turing-synthetic-radar-dataset",
        repo_type="dataset"
    )
    
    h5_files = [f for f in files if f.endswith('.h5')]
    print(f"   Found {len(h5_files)} H5 files")
    
    # Show sample
    if h5_files:
        print(f"\n   Sample files:")
        for f in h5_files[:10]:
            print(f"   - {f}")
    
    return h5_files


def download_files(file_list, output_dir="data/tsrd_real", max_files=10):
    """Download actual TSRD files."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📥 Downloading {min(max_files, len(file_list))} files...")
    
    downloaded = []
    for i, file_path in enumerate(file_list[:max_files]):
        try:
            print(f"   [{i+1}/{min(max_files, len(file_list))}] {file_path}")
            
            local_path = hf_hub_download(
                repo_id="alan-turing-institute/turing-synthetic-radar-dataset",
                filename=file_path,
                repo_type="dataset",
                local_dir=output_dir
            )
            downloaded.append(local_path)
            print(f"      ✅ Downloaded")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Create metadata
    metadata = {
        'files': downloaded,
        'count': len(downloaded),
        'source': 'tsrd_real'
    }
    
    with open(f'{output_dir}/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Downloaded {len(downloaded)} files to {output_dir}/")
    return downloaded


def inspect_file(file_path):
    """Inspect a downloaded H5 file."""
    try:
        with h5py.File(file_path, 'r') as f:
            print(f"\n📊 Inspecting: {os.path.basename(file_path)}")
            print(f"   Keys: {list(f.keys())}")
            
            # Try to understand structure
            if 'pulses' in f:
                pulses = f['pulses']
                print(f"   Pulses shape: {pulses.shape}")
                
                # Check if there's more structure
                if hasattr(pulses, 'attrs'):
                    print(f"   Attributes: {dict(pulses.attrs)}")
            
            if 'labels' in f:
                labels = f['labels']
                print(f"   Labels: {labels[:20] if len(labels) > 20 else labels}")
            
            # Look for other datasets
            other_keys = [k for k in f.keys() if k not in ['pulses', 'labels']]
            if other_keys:
                print(f"   Other keys: {other_keys}")
                
    except Exception as e:
        print(f"   ❌ Error inspecting: {e}")


def main():
    print("=" * 60)
    print("REAL TSRD DOWNLOADER")
    print("=" * 60)
    
    # Step 1: List available files
    h5_files = list_available_files()
    
    if not h5_files:
        print("\n❌ No H5 files found. The repository structure might be different.")
        print("   Creating demo data instead...")
        create_demo_data()
        return
    
    # Step 2: Download some files
    downloaded = download_files(h5_files, max_files=10)
    
    # Step 3: Inspect first file
    if downloaded:
        inspect_file(downloaded[0])


def create_demo_data():
    """Create demo data as fallback."""
    output_dir = "data/tsrd_real"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n🔧 Creating demo files in {output_dir}...")
    
    # Create 10 demo files
    for i in range(10):
        file_path = f'{output_dir}/demo_train_{i+1:04d}.h5'
        
        with h5py.File(file_path, 'w') as f:
            num_pulses = np.random.randint(100, 1000)
            num_emitters = np.random.randint(2, 8)
            
            pulses = np.zeros((num_pulses, 5))
            pulses[:, 0] = np.cumsum(np.random.exponential(0.01, num_pulses))  # ToA
            pulses[:, 1] = np.random.uniform(8000, 12000, num_pulses)  # CF
            pulses[:, 2] = np.random.uniform(0.5, 3.0, num_pulses)  # PW
            pulses[:, 3] = np.random.uniform(0, 360, num_pulses)  # AoA
            pulses[:, 4] = np.random.uniform(0.1, 1.0, num_pulses)  # Amplitude
            
            f.create_dataset('pulses', data=pulses)
            f.create_dataset('labels', data=np.random.randint(0, num_emitters, num_pulses))
    
    print(f"   ✅ Created 10 demo files")
    print(f"   Location: {output_dir}/")


if __name__ == "__main__":
    main()
