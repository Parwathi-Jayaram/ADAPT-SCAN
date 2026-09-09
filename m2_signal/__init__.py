# m2_signal/__init__.py

from .m2_interface import M2Interface, generate_observation
from .signal_generator import generate_signal
from .noise_model import get_noise_config, apply_noise
from .observation import ObservationModel, Observation, create_observation
from .feature_extractor import FeatureExtractor, ExtractedFeatures

# Integration bridge
from .m3_integration import M2M3Bridge, scan, scan_all

__all__ = [
    'M2Interface',
    'generate_observation',
    'generate_signal',
    'get_noise_config',
    'apply_noise',
    'ObservationModel',
    'Observation',
    'create_observation',
    'FeatureExtractor',
    'ExtractedFeatures',
    'M2M3Bridge',
    'scan',
    'scan_all',
]