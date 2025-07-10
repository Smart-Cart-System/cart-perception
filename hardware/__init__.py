"""
Hardware interface components for the cart perception system.
Provides classes for interacting with physical hardware devices.
"""

from .weight_tracking import WeightTracker
from .camera import set_camera_properties, calculate_focus_measure
from .speaker import SpeakerUtil
from .led import LEDController
from .gpio_manager import gpio

__all__ = ['WeightTracker', 'set_camera_properties', 'calculate_focus_measure', 'SpeakerUtil', 'LEDController', 'gpio']
