"""
M2-M3 Integration Bridge - FINAL FIXED VERSION
Connects M3's simulator output to M2's interface
"""

from typing import Dict, Any, Optional, List, cast
import time

# Conditional imports - works both as package and when run directly
try:
    from .m2_interface import M2Interface
except ImportError:
    from m2_interface import M2Interface

# Try importing M3's simulator
try:
    from m3_simulator.simulator import Environment
    from m3_simulator.simulator.tsrd_real_adapter import TSRDRealAdapter
    M3_AVAILABLE = True
except ImportError:
    M3_AVAILABLE = False
    print("⚠️ M3 simulator not available. Running in mock mode.")


class M2M3Bridge:
    """
    Bridge between M3's Environment and M2's Interface.
    """
    
    def __init__(self, 
                 noise_level: str = "medium",
                 seed: Optional[int] = 42,
                 num_regions: int = 20,
                 use_real_data: bool = False,
                 data_dir: str = "data/tsrd_real",
                 m3_available: bool = M3_AVAILABLE):
        """
        Initialize the bridge.
        """
        self.m3_available = m3_available
        self.noise_level = noise_level
        self.seed = seed if seed is not None else 42
        self.num_regions = num_regions
        self.use_real_data = use_real_data
        self.data_dir = data_dir
        
        # Initialize M2 interface
        self.m2 = M2Interface(noise_level=noise_level, seed=self.seed)
        
        self.env = None
        self.adapter = None
        self._last_m3_obs = None
        self._last_m3_info = None
        
        if self.m3_available:
            try:
                self._initialize_environment()
                print("✅ M3 Environment initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize M3 Environment: {e}")
                self.m3_available = False
                self.env = None
        else:
            self.env = None
    
    def _initialize_environment(self):
        """Initialize the M3 environment."""
        self.env = Environment(num_regions=self.num_regions, seed=self.seed)
        
        if self.use_real_data:
            try:
                self.adapter = TSRDRealAdapter(data_dir=self.data_dir)
                
                # Use setattr to bypass type checking
                setattr(self.env, 'tsrd_adapter', self.adapter)
                setattr(self.env, 'using_real_data', True)
                
                print(f"✅ Using real TSRD data from {self.data_dir}")
            except Exception as e:
                print(f"⚠️ Failed to load TSRD data: {e}")
    
    def reset_scenario(self, scenario_id: str = "S1", seed: Optional[int] = None) -> Dict[str, Any]:
        """Reset the environment to a specific scenario."""
        if self.env is None:
            return {"error": "Environment not initialized"}
        
        actual_seed = seed if seed is not None else self.seed
        obs = self.env.reset(scenario_id, seed=actual_seed)
        return obs
    
    def scan_region(self, region_id: str) -> Dict[str, Any]:
        if self.m3_available and self.env is not None:
            try:
                m3_obs, reward, done, info = self.env.step(region_id)
                scan_result = info.get('scan_result')
                if scan_result:
                    scanner_result = {
                        "region_id": region_id,
                        "signal_type": self._classify_signal(
                            getattr(scan_result, 'strength', 0.5),
                            getattr(scan_result, 'bandwidth', 0.3),
                            getattr(scan_result, 'snr', 5.0)
                        ),
                        "scan_mode": "standard",
                        "additional_cost": getattr(scan_result, 'scan_cost', 1.0)
                    }
                else:
                    scanner_result = {"region_id": region_id}
            except Exception as e:
                print(f"⚠️ M3 step failed for {region_id}: {e}")
                scanner_result = {"region_id": region_id}
        else:
            # ✅ FIX: Same path as direct M2Interface
            scanner_result = {"region_id": region_id}
        
        return self.m2.generate_observation(scanner_result)
    
    def _classify_signal(self, strength: float, bandwidth: float, snr: float) -> str:
        """Classify signal type based on raw parameters."""

        if strength > 0.7 and snr > 10:
            return "continuous"

        elif strength > 0.4 and snr > 5:
            return "changing-strength"

        elif bandwidth > 0.5:
            return "noisy"

        else:
            return "intermittent"
    
    def process_raw_scan(self, scan_result, region_id: str) -> Dict[str, Any]:
        """Process a raw ScanResult object from M3 directly."""
        scanner_result = {
            "region_id": region_id,
            "signal_type": self._classify_signal(
                getattr(scan_result, 'strength', 0.5),
                getattr(scan_result, 'bandwidth', 0.3),
                getattr(scan_result, 'snr', 5.0)
            ),
            "scan_mode": "standard",
            "additional_cost": getattr(scan_result, 'scan_cost', 1.0)
        }
        return self.m2.generate_observation(scanner_result)
    
    def scan_multiple_regions(self, region_ids: List[str]) -> List[Dict[str, Any]]:
        """Scan multiple regions and return processed observations."""
        return [self.scan_region(region_id) for region_id in region_ids]
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get status of the M3 environment."""
        return {
            "m3_available": self.m3_available,
            "env_initialized": self.env is not None,
            "m2_ready": True,
            "using_real_data": self.use_real_data if self.env else False,
            "num_regions": self.num_regions
        }


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def scan(
    region_id: str,
    noise_level: str = "medium",
    seed: Optional[int] = 42,
    use_real_data: bool = False
) -> Dict[str, Any]:
    """
    Scan one region using a fresh M3 scenario
    and process the result through M2.
    """

    actual_seed = seed if seed is not None else 42

    bridge = M2M3Bridge(
        noise_level=noise_level,
        seed=actual_seed,
        use_real_data=use_real_data
    )

    # Initialize the M3 scenario before scanning.
    bridge.reset_scenario(
        scenario_id="S1",
        seed=actual_seed
    )

    return bridge.scan_region(region_id)

def scan_all(
    region_ids: List[str],
    noise_level: str = "medium",
    seed: Optional[int] = 42,
    use_real_data: bool = False
) -> List[Dict[str, Any]]:
    """
    Scan multiple regions using the same M3 scenario
    and process all results through M2.
    """

    actual_seed = seed if seed is not None else 42

    bridge = M2M3Bridge(
        noise_level=noise_level,
        seed=actual_seed,
        use_real_data=use_real_data
    )

    # Initialize the M3 scenario once.
    bridge.reset_scenario(
        scenario_id="S1",
        seed=actual_seed
    )

    return bridge.scan_multiple_regions(region_ids)

# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("M2-M3 INTEGRATION TEST")
    print("=" * 60)
    
    print("\n1. Testing bridge with mock mode:")
    bridge = M2M3Bridge(m3_available=False)
    
    print("\n   Single region scan:")
    obs = bridge.scan_region("R7")
    print(f"   Region: {obs['region_id']}")
    print(f"   Detected: {obs['detected']}")
    print(f"   Confidence: {obs['confidence']:.3f}")
    print(f"   Confidence Level: {obs['confidence_level']}")
    
    print("\n   Multiple regions scan:")
    regions = ["R1", "R2", "R3", "R4", "R5"]
    results = bridge.scan_multiple_regions(regions)
    
    for result in results:
        status = "✅" if result['detected'] else "❌"
        print(f"   {status} {result['region_id']}: "
              f"conf={result['confidence']:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ M2-M3 Bridge ready for integration!")
    print("=" * 60)