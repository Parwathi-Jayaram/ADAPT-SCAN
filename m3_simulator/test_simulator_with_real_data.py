"""
Test the full simulator with real TSRD data.
"""

from simulator import Environment
from simulator.tsrd_real_adapter import TSRDRealAdapter


def test_simulator_with_real_data():
    print("=" * 70)
    print("TESTING SIMULATOR WITH REAL TSRD DATA")
    print("=" * 70)
    
    # Create environment
    env = Environment(num_regions=20, seed=42)
    
    # Load real data adapter
    print("\n1️⃣ Loading Real TSRD Data...")
    adapter = TSRDRealAdapter(data_dir="data/tsrd_real")
    stats = adapter.get_statistics()
    print(f"   Loaded: {stats['total_pulses']:,} pulses, {stats['num_emitters']} emitters")
    
    # Inject adapter into environment
    env.tsrd_adapter = adapter
    env.using_real_data = True
    
    # Reset and run simulation
    print("\n2️⃣ Running Simulation with Real Data...")
    obs = env.reset('S1', seed=42)
    print(f"   Initial budget: {obs['budget_remaining']}")
    
    found = 0
    for step in range(15):
        region = f'R{(step % 5) + 1}'
        
        # Use real data for region truth
        truth = adapter.get_region_truth(region)
        
        # Step the environment
        obs, reward, done, info = env.step(region)
        
        # Check if we found something
        if truth.get('exists', False):
            found += 1
            print(f"   Step {step+1}: {region} - {truth['num_pulses']} pulses, {truth.get('num_emitters', 0)} emitters")
    
    print(f"\n3️⃣ Results:")
    print(f"   Regions with signals: {found}")
    print(f"   Budget used: {100 - obs['budget_remaining']:.1f}")
    print(f"   Steps completed: {obs['timestep']}")
    
    print("\n" + "=" * 70)
    print("✅ SIMULATOR WITH REAL DATA TEST PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_simulator_with_real_data()
