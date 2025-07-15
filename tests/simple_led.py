import sys
import os

# Add the parent directory to the path so we can import from hardware
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.led import LEDController
import time

# Test function
def test_led_controller():
    """Test function for LED controller."""
    led = LEDController()
    
    try:
        print("Setting LED to green...")
        led.white(100)
        time.sleep(3)
        led.start_loading_animation()
        time.sleep(10)
        led.white(100)
        # Keep the program running
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        led.cleanup()

if __name__ == "__main__":
    print("Starting LED controller test...")
    test_led_controller()
