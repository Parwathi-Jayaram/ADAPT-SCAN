"""
Test the real TSRD adapter with downloaded files.
"""

from simulator.tsrd_real_adapter import TSRDRealAdapter


def test_adapter():
    print("=" * 70)
    print("TESTING REAL TSRD ADAPTER")
    print("=" * 70)
    
    # Initialize adapter
    print("\n1️⃣ Initializing adapter...")
    adapter = TSRDRealAdapter(data_dir="data/tsrd_real")
    
    # Get statistics
    stats = adapter.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total pulses: {stats.get('total_pulses', 0)}")
    print(f"   Num features: {stats.get('num_features', 0)}")
    print(f"   Num emitters: {stats.get('num_emitters', 0)}")
    print(f"   Current file: {stats.get('file', 'unknown')}")
    
    # Test region queries
    print("\n2️⃣ Testing region queries:")
    for region in ['R1', 'R3', 'R5', 'R7', 'R10', 'R12', 'R15', 'R18', 'R20']:
        result = adapter.get_region_truth(region)
        if result.get('exists', False):
            print(f"   ✅ {region}: {result['num_pulses']} pulses, {result.get('num_emitters', 0)} emitters")
        else:
            print(f"   ❌ {region}: No signals")
    
    # Test switching files
    print("\n3️⃣ Testing file switching:")
    for i in range(3):
        adapter.switch_file()
        stats = adapter.get_statistics()
        print(f"   File {i+1}: {stats.get('file', 'unknown')} - {stats.get('total_pulses', 0)} pulses")
    
    print("\n" + "=" * 70)
    print("✅ REAL TSRD ADAPTER TEST PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_adapter()
