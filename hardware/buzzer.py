import RPi.GPIO as GPIO
import threading
import time

class BuzzerUtil:
    """Utility class for playing different buzzer sounds for cart events."""
    
    def __init__(self, buzzer_pin=23):
        """Initialize the buzzer interface."""
        self.buzzer_pin = buzzer_pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        self.is_busy = False
        self.stop_requested = False
        GPIO.output(self.buzzer_pin, GPIO.LOW)  # Ensure buzzer is off initially
    
    def _play_pattern(self, pattern):
        """Play a specific beep pattern.
        
        Args:
            pattern: List of tuples (state, duration) where state is GPIO.HIGH/LOW
                    and duration is time in seconds.
        """
        self.stop_requested = False
        self.is_busy = True
        
        for state, duration in pattern:
            if self.stop_requested:
                break
                
            GPIO.output(self.buzzer_pin, state)
            time.sleep(duration)
        
        # Ensure buzzer is turned off after pattern completes
        GPIO.output(self.buzzer_pin, GPIO.LOW)
        self.is_busy = False
    
    def play_async(self, pattern):
        """Play a sound pattern in a separate thread."""
        if self.is_busy:
            self.stop()  # Stop any currently playing pattern
            time.sleep(0.1)  # Small delay to ensure it stops
            
        thread = threading.Thread(target=self._play_pattern, args=(pattern,), daemon=True)
        thread.start()
    
    def stop(self):
        """Stop any currently playing pattern."""
        if self.is_busy:
            self.stop_requested = True
            GPIO.output(self.buzzer_pin, GPIO.LOW)
    
    # Pre-defined sound patterns
    def item_scanned(self):
        """Sound for when an item barcode is scanned."""
        pattern = [(GPIO.HIGH, 0.05), (GPIO.LOW, 0.05)]
        self.play_async(pattern)
    
    def item_added(self):
        """Sound for when an item is added to cart."""
        pattern = [(GPIO.HIGH, 0.05), (GPIO.LOW, 0.05), (GPIO.HIGH, 0.05), (GPIO.LOW, 0.05)]
        self.play_async(pattern)
    
    def item_removed(self):
        """Sound for when an item is removed from cart."""
        pattern = [(GPIO.HIGH, 0.2), (GPIO.LOW, 0.1), (GPIO.HIGH, 0.1), (GPIO.LOW, 0.05)]
        self.play_async(pattern)
    
    def error_occurred(self):
        """Sound for when an error occurs."""
        pattern = [
            (GPIO.HIGH, 0.2), (GPIO.LOW, 0.1),
            (GPIO.HIGH, 0.2), (GPIO.LOW, 0.1),
            (GPIO.HIGH, 0.3), (GPIO.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def waiting_for_scan(self):
        """Sound to indicate waiting for barcode scan."""
        pattern = [
            (GPIO.HIGH, 0.05), (GPIO.LOW, 0.2),
            (GPIO.HIGH, 0.05), (GPIO.LOW, 0.2),
            (GPIO.HIGH, 0.05), (GPIO.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def ambiguous_removal(self):
        """Sound for ambiguous item removal."""
        pattern = [
            (GPIO.HIGH, 0.1), (GPIO.LOW, 0.1),
            (GPIO.HIGH, 0.1), (GPIO.LOW, 0.1),
            (GPIO.HIGH, 0.3), (GPIO.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def cleanup(self):
        """Clean up resources, should be called before program exit."""
        self.stop()
        # Don't call GPIO.cleanup() here as it might be needed by other components


# Simple test if this file is run directly
if __name__ == "__main__":
    buzzer = BuzzerUtil()
    
    print("Testing item scanned sound...")
    buzzer.item_scanned()
    time.sleep(1)
    
    print("Testing item added sound...")
    buzzer.item_added()
    time.sleep(1)
    
    print("Testing item removed sound...")
    buzzer.item_removed()
    time.sleep(1)
    
    print("Testing error sound...")
    buzzer.error_occurred()
    time.sleep(1.5)
    
    print("Testing waiting for scan sound...")
    buzzer.waiting_for_scan()
    time.sleep(1.5)
    
    print("Testing ambiguous removal sound...")
    buzzer.ambiguous_removal()
    time.sleep(1.5)
    
    print("Test complete!")
    GPIO.cleanup()