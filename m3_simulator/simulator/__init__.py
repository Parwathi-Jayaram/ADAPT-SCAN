"""
ADAPT-SCAN Simulator Module.

Provides the simulation environment for the ADAPT-SCAN project.
"""

from .environment import Environment
from .emitter import Emitter
from .scanner import Scanner, ScanResult
from .ground_truth import GroundTruth
from .noise_model import NoiseModel
from .scenarios import get_scenario_config, SCENARIO_CONFIGS, list_scenarios

__version__ = "0.1.0"

__all__ = [
    "Environment",
    "Emitter",
    "Scanner",
    "ScanResult",
    "GroundTruth",
    "NoiseModel",
    "get_scenario_config",
    "SCENARIO_CONFIGS",
    "list_scenarios"
]
