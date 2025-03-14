"""
Hardware interface components for the cart perception system.
Provides classes for interacting with physical hardware devices.
"""

from .buzzer import BuzzerUtil
from .weight_tracking import WeightTracker
from .camera import set_camera_properties

__all__ = ['BuzzerUtil', 'WeightTracker', 'set_camera_properties']
