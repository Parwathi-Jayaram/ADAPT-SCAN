import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m3_integration import scan_all

results = scan_all(["R1", "R2", "R3", "R4", "R5"])

print(f"{'Region':<8} {'Detected':<10} {'Strength':<10} {'Confidence':<12} {'Level':<12} {'Uncertainty':<12}")
print("-" * 70)

for r in results:
    print(
        f"{r['region_id']:<8} "
        f"{str(r['detected']):<10} "
        f"{r['strength']:<10.3f} "
        f"{r['confidence']:<12.3f} "
        f"{r['confidence_level']:<12} "
        f"{r['features'][4]:<12.3f}"
    )