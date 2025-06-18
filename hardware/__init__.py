"""
Hardware interface components for the cart perception system.
Provides classes for interacting with physical hardware devices.
"""

from .buzzer import BuzzerUtil
from .weight_tracking import WeightTracker
from .camera import set_camera_properties
from .speaker import SpeakerUtil
from .led import LEDUtil

__all__ = ['BuzzerUtil', 'WeightTracker', 'set_camera_properties', 'SpeakerUtil', 'LEDUtil']
