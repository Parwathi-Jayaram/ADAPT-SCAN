# m2_signal/__init__.py
"""
Member 2 - Signal Processing Module
"""

from .signal_generator import generate_signal
from .noise_model import get_noise_config, apply_noise
from .observation import Observation, ObservationModel, create_observation
from .feature_extractor import FeatureExtractor, ExtractedFeatures

__all__ = [
    'generate_signal',
    'get_noise_config',
    'apply_noise',
    'Observation',
    'ObservationModel',
    'create_observation',
    'FeatureExtractor',
    'ExtractedFeatures',
]