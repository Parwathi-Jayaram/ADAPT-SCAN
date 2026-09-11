import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m2_interface import M2Interface

m2 = M2Interface(noise_level="medium", seed=42)
obs = m2.generate_observation({"region_id": "R7"})
print("Direct M2Interface output:")
print(obs)