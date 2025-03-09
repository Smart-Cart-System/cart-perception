import time
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

class WeightTracker:
    """Class for tracking weight changes using HX711 sensor."""
    
    def __init__(self, dout_pin=5, pd_sck_pin=6, reference_unit=216, weight_threshold=10):
        """Initialize the weight tracking system."""
        self.hx = HX711(dout_pin, pd_sck_pin)
        self.hx.setReadingFormat("MSB", "MSB")
        self.hx.autosetOffset()
        self.hx.setReferenceUnit(reference_unit)
        self.last_weight = 0
        self.weight_threshold = weight_threshold  # Minimum weight change to detect (grams)
        print("[INFO] Weight tracking system initialized")
        
    def get_current_weight(self):
        """Get current weight reading."""
        readings = []
        for _ in range(5):  # Take multiple readings for stability
            rawBytes = self.hx.getRawBytes()
            weight = max(0, self.hx.rawBytesToWeight(rawBytes))  # Ensure non-negative
            readings.append(weight)
            time.sleep(0.1)
        
        # Return the average after removing outliers
        return sum(readings) / len(readings)
    
    def get_weight_change(self):
        """Get the change in weight since the last stable reading."""
        current_weight = self.get_current_weight()
        weight_diff = current_weight - self.last_weight
        
        # Only report significant weight changes
        if abs(weight_diff) >= self.weight_threshold:
            self.last_weight = current_weight
            return weight_diff
        
        return 0
    
    def wait_for_stable_weight(self, stability_time=1.0):
        """Wait until weight readings stabilize."""
        readings = []
        start_time = time.time()
        
        while time.time() - start_time < stability_time:
            readings.append(self.get_current_weight())
            time.sleep(0.2)
            
        # Return the average of the last few readings
        return sum(readings) / len(readings)
    
    def reset(self):
        """Reset the weight tracker."""
        self.last_weight = 0
        self.hx.autosetOffset()
        
    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup()