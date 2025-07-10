import threading
import time
from hardware.gpio_manager import gpio

class BuzzerUtil:
    """Utility class for playing different buzzer sounds for cart events."""
    
    def __init__(self, buzzer_pin=23):
        """Initialize the buzzer interface."""
        self.buzzer_pin = buzzer_pin
        gpio.setup(self.buzzer_pin, gpio.OUT)
        self.is_busy = False
        self.stop_requested = False
        gpio.output(self.buzzer_pin, gpio.LOW)  # Ensure buzzer is off initially
    
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
                
            gpio.output(self.buzzer_pin, state)
            time.sleep(duration)
        
        # Ensure buzzer is turned off after pattern completes
        gpio.output(self.buzzer_pin, gpio.LOW)
        self.is_busy = False
    
    def play_async(self, pattern):
        """Play a sound pattern in a separate thread."""
        if self.is_busy:
            self.stop()  # Stop any currently playing pattern
            time.sleep(0.1)  # Small delay to ensure it stops
            
        thread = threading.Thread(target=self._play_pattern, args=(pattern,), daemon=True, name="BuzzerThread")
        thread.start()
    
    def stop(self):
        """Stop any currently playing pattern."""
        if self.is_busy:
            self.stop_requested = True
            gpio.output(self.buzzer_pin, gpio.LOW)
    
    # Pre-defined sound patterns
    def item_scanned(self):
        """Sound for when an item barcode is scanned."""
        pattern = [(gpio.HIGH, 0.05), (gpio.LOW, 0.05)]
        self.play_async(pattern)
    
    def item_added(self):
        """Sound for when an item is added to cart."""
        pattern = [(gpio.HIGH, 0.05), (gpio.LOW, 0.05), (gpio.HIGH, 0.05), (gpio.LOW, 0.05)]
        self.play_async(pattern)
    
    def item_removed(self):
        """Sound for when an item is removed from cart."""
        pattern = [(gpio.HIGH, 0.2), (gpio.LOW, 0.1), (gpio.HIGH, 0.1), (gpio.LOW, 0.05)]
        self.play_async(pattern)
    
    def error_occurred(self):
        """Sound for when an error occurs."""
        pattern = [
            (gpio.HIGH, 0.2), (gpio.LOW, 0.1),
            (gpio.HIGH, 0.2), (gpio.LOW, 0.1),
            (gpio.HIGH, 0.3), (gpio.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def waiting_for_scan(self):
        """Sound to indicate waiting for barcode scan."""
        pattern = [
            (gpio.HIGH, 0.05), (gpio.LOW, 0.2),
            (gpio.HIGH, 0.05), (gpio.LOW, 0.2),
            (gpio.HIGH, 0.05), (gpio.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def ambiguous_removal(self):
        """Sound for ambiguous item removal."""
        pattern = [
            (gpio.HIGH, 0.1), (gpio.LOW, 0.1),
            (gpio.HIGH, 0.1), (gpio.LOW, 0.1),
            (gpio.HIGH, 0.3), (gpio.LOW, 0.05)
        ]
        self.play_async(pattern)
    
    def cleanup(self):
        """Clean up resources, should be called before program exit."""
        self.stop()
        # Don't cleanup GPIO pin, let the manager handle it


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
    gpio.cleanup()