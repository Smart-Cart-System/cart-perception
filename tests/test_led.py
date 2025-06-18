from hardware.led import LEDController
import time

# Test function
def test_led_controller():
    """Test function for LED controller."""
    led = LEDController()
    
    try:
        print("Testing LED colors...")
        
        # Test basic colors
        led.red(100)
        time.sleep(2)
        
        led.green(100)
        time.sleep(2)
        
        led.blue(100)
        time.sleep(2)
        
        led.yellow(100)
        time.sleep(2)
        
        led.orange(100)
        time.sleep(2)
        
        led.white(50)
        time.sleep(2)
        
        # Test blinking
        print("Testing blink...")
        led.blink(led.red, intensity=100, blink_count=5, blink_speed=0.3)
        time.sleep(4)
        
        # Test pulsing
        print("Testing pulse...")
        led.pulse(led.blue, max_intensity=100, pulse_speed=0.05, duration=3)
        time.sleep(4)
        
        led.off()
        
        # Test loading animation
        print("Testing loading animation...")
        led.loading(max_intensity=100, fade_speed=0.01, duration=5)
        time.sleep(6)
        
        led.off()
        
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        led.cleanup()
