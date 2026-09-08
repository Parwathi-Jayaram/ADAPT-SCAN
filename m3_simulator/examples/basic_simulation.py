"""Basic simulation example using the ADAPT-SCAN simulator."""

from simulator import Environment
import random


def run_simulation(scenario='S2', seed=42, max_steps=30):
    """Run a basic simulation with a simple strategy."""
    
    print("=" * 60)
    print("ADAPT-SCAN Simulation Demo")
    print("=" * 60)
    
    env = Environment(num_regions=20, seed=seed)
    obs = env.reset(scenario, seed=seed)
    
    print(f"\nScenario: {scenario}")
    print(f"Budget: {obs['budget_remaining']}")
    
    # Simple strategy: scan regions with highest uncertainty
    steps = 0
    total_reward = 0
    detected_regions = set()
    
    while not env.done and steps < max_steps:
        # Get regions sorted by uncertainty
        regions = obs['regions']
        uncertain = sorted(
            [r for r in regions if r.get('uncertainty', 0) > 0.3],
            key=lambda x: x.get('uncertainty', 0),
            reverse=True
        )
        
        # Scan most uncertain or random
        if uncertain:
            action = uncertain[0]['region_id']
        else:
            action = f'R{random.randint(1, 20)}'
        
        # Execute scan
        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        
        # Track detections
        for region in obs['regions']:
            if region.get('detected', False):
                detected_regions.add(region['region_id'])
        
        # Show progress
        if steps % 5 == 0:
            print(f"  Step {steps}: Budget={obs['budget_remaining']:.1f}, "
                  f"Detected={len(detected_regions)}, Reward={total_reward:.2f}")
    
    print(f"\n✅ Simulation complete!")
    print(f"  Steps: {steps}")
    print(f"  Total reward: {total_reward:.2f}")
    print(f"  Detected regions: {len(detected_regions)}")
    print(f"  Budget used: {100 - obs['budget_remaining']:.1f}")
    
    return {
        'steps': steps,
        'reward': total_reward,
        'detected': len(detected_regions),
        'budget_used': 100 - obs['budget_remaining']
    }


if __name__ == "__main__":
    run_simulation()
