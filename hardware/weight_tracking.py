import time
import threading
import statistics
import RPi.GPIO as GPIO
from hardware.hx711v0_5_1 import HX711
from collections import deque

class WeightTracker:
    """Class for tracking weight changes using HX711 sensor with background thread."""
    
    def __init__(self, dout_pin=5, pd_sck_pin=6, reference_unit=216, weight_threshold=15):
        """Initialize the weight tracking system with background thread."""
        # Initialize HX711 sensor
        self.hx = HX711(dout_pin, pd_sck_pin)
        self.hx.setReadingFormat("MSB", "MSB")
        self.hx.autosetOffset()
        self.hx.setReferenceUnit(reference_unit)
        
        # Thread control variables
        self.running = True
        self.lock = threading.Lock()
        
        # Weight tracking variables
        self.last_weight = 0
        self.current_weight = 0
        self.weight_threshold = weight_threshold
        
        # Buffer for recent weight readings
        self.recent_readings = deque(maxlen=10)
        
        # Start background thread
        self.thread = threading.Thread(target=self._weight_monitoring_thread, daemon=True)
        self.thread.start()
        
        print("[INFO] Weight tracking system initialized (threaded mode)")
    
    def _weight_monitoring_thread(self):
        """Background thread for continuous weight monitoring."""
        while self.running:
            try:
                # Get raw weight reading
                rawBytes = self.hx.getRawBytes()
                weight = max(0, self.hx.rawBytesToWeight(rawBytes))
                
                # Add to recent readings
                with self.lock:
                    self.recent_readings.append(weight)
                    
                    # Calculate current weight (median for robustness against outliers)
                    if len(self.recent_readings) >= 3:
                        self.current_weight = statistics.median(self.recent_readings)
                
                # Small sleep to avoid overwhelming the HX711
                time.sleep(0.05)
                
            except Exception as e:
                print(f"[ERROR] Weight sensor thread error: {e}")
                time.sleep(0.5)  # Delay before retrying
    
    def get_current_weight(self):
        """Get current weight reading (non-blocking)."""
        with self.lock:
            return self.current_weight
    
    def get_weight_change(self, wait_time=1.0, stability_threshold=2.0):
        """
        Wait for a stable weight reading for a given time before calculating the weight difference.
        :param wait_time: Duration (in seconds) to wait for stability.
        :param stability_threshold: Acceptable range for weight fluctuations during stability check.
        :return: The weight difference if it exceeds the threshold, otherwise 0.
        """
        # Wait until weight readings stabilize over the specified wait_time
        stable_weight = self.wait_for_stable_weight(stability_time=wait_time, stability_threshold=stability_threshold)
        
        # Calculate the difference from the last stable reading
        weight_diff = stable_weight - self.last_weight
        
        # Report the difference only if it's significant
        if abs(weight_diff) >= self.weight_threshold:
            with self.lock:
                self.last_weight = stable_weight
            return weight_diff

        return 0

    
    def wait_for_stable_weight(self, stability_time=1.0, stability_threshold=2.0):
        """Wait until weight readings stabilize."""
        start_time = time.time()
        readings = []
        
        while time.time() - start_time < stability_time:
            current = self.get_current_weight()
            readings.append(current)
            
            # Check if recent readings are stable
            if len(readings) >= 3 and max(readings[-3:]) - min(readings[-3:]) < stability_threshold:
                return statistics.mean(readings[-3:])
                
            time.sleep(0.1)  # Small sleep is ok here since it's an explicit waiting function
            
        # Return the median of collected readings if we timeout
        return statistics.median(readings) if readings else 0
    
    def reset(self):
        """Reset the weight tracker."""
        with self.lock:
            self.last_weight = 0
            self.recent_readings.clear()
        self.hx.autosetOffset()
        
    def cleanup(self):
        """Clean up resources."""
        self.running = False  # Signal thread to stop
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)  # Wait for thread to end
        GPIO.cleanup()