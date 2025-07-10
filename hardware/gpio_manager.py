"""
Centralized GPIO Management Module
==================================

This module provides centralized access to RPi.GPIO functionality to prevent
initialization conflicts between different components.
"""

import RPi.GPIO as GPIO
import threading
import logging

logger = logging.getLogger(__name__)

class GPIOManager:
    """Singleton class to manage GPIO access across the application."""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GPIOManager, cls).__new__(cls)
                cls._instance._init_gpio()
            return cls._instance
    
    def _init_gpio(self):
        """Initialize GPIO with BCM mode if not already initialized."""
        if not self._initialized:
            logger.info("Initializing GPIO in BCM mode")
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            self._initialized = True
            # Dictionary to track active PWM objects
            self._pwm_objects = {}
    
    @property
    def gpio(self):
        """Get the GPIO module."""
        return GPIO
    
    def setup(self, pin, mode, **kwargs):
        """Set up a GPIO pin."""
        return GPIO.setup(pin, mode, **kwargs)
    
    def output(self, pin, value):
        """Set a GPIO pin output value."""
        return GPIO.output(pin, value)
    
    def input(self, pin):
        """Read a GPIO pin input value."""
        return GPIO.input(pin)
    
    def cleanup(self, pin=None):
        """Clean up GPIO resources."""
        # Stop any active PWM objects first
        if pin is None:
            logger.info("Cleaning up all GPIO resources")
            # Stop all PWM objects before cleanup
            for pwm_pin in list(self._pwm_objects.keys()):
                self.stop_pwm(pwm_pin)
        else:
            logger.info(f"Cleaning up GPIO pin {pin}")
            # Stop PWM for this pin if it exists
            self.stop_pwm(pin)
            
        return GPIO.cleanup(pin)
    
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        """Add event detection to a GPIO pin."""
        return GPIO.add_event_detect(pin, edge, callback=callback, bouncetime=bouncetime)
    
    def remove_event_detect(self, pin):
        """Remove event detection from a GPIO pin."""
        return GPIO.remove_event_detect(pin)
    
    def create_pwm(self, pin, frequency):
        """Create or get an existing PWM instance for a pin.
        
        This ensures we don't create duplicate PWM objects for the same pin.
        """
        pin_key = str(pin)  # Use string keys for consistency
        
        # Check if PWM object already exists for this pin
        if pin_key in self._pwm_objects:
            logger.info(f"Returning existing PWM object for pin {pin}")
            # If frequency changed, we need to recreate the PWM object
            current_pwm = self._pwm_objects[pin_key]
            # Unfortunately, we can't check the frequency of an existing PWM object
            # so we'll trust the caller
            return current_pwm
        
        # Create new PWM object
        logger.info(f"Creating new PWM object for pin {pin} with frequency {frequency}")
        pwm = GPIO.PWM(pin, frequency)
        self._pwm_objects[pin_key] = pwm
        return pwm
    
    def stop_pwm(self, pin):
        """Stop and remove a PWM object for a pin."""
        pin_key = str(pin)
        if pin_key in self._pwm_objects:
            logger.info(f"Stopping PWM for pin {pin}")
            try:
                self._pwm_objects[pin_key].stop()
            except Exception as e:
                logger.error(f"Error stopping PWM for pin {pin}: {e}")
            del self._pwm_objects[pin_key]
            return True
        return False
    
    def is_pwm_active(self, pin):
        """Check if a PWM object is active for a pin."""
        return str(pin) in self._pwm_objects
    
    # GPIO constants
    @property
    def OUT(self):
        return GPIO.OUT
    
    @property
    def IN(self):
        return GPIO.IN
    
    @property
    def HIGH(self):
        return GPIO.HIGH
    
    @property
    def LOW(self):
        return GPIO.LOW
    
    @property
    def RISING(self):
        return GPIO.RISING
    
    @property
    def FALLING(self):
        return GPIO.FALLING
    
    @property
    def BOTH(self):
        return GPIO.BOTH
    
    @property
    def PUD_UP(self):
        return GPIO.PUD_UP
    
    @property
    def PUD_DOWN(self):
        return GPIO.PUD_DOWN

# Create a singleton instance
gpio = GPIOManager()
