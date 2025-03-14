import sys
import RPi.GPIO as GPIO
from core.cart_system import CartSystem

def main():
    """Main entry point for the cart perception system."""
    try:
        cart_system = CartSystem(cart_id=1)
        cart_system.run()
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        GPIO.cleanup()

if __name__ == "__main__":
    main()