import RPi.GPIO as GPIO
import time

# Define pins
RED_PIN = 17
GREEN_PIN = 27
BLUE_PIN = 22

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

def set_color_logic(r, g, b):
    """Use logic high/low to drive pins instead of PWM."""
    GPIO.output(RED_PIN, GPIO.HIGH if r else GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH if g else GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.HIGH if b else GPIO.LOW)

try:
    print("Testing logic control")
    set_color_logic(1, 0, 0)  # Red
    time.sleep(2)
    set_color_logic(0, 1, 0)  # Green
    time.sleep(2)
    set_color_logic(0, 0, 1)  # Blue
    time.sleep(2)
    set_color_logic(0, 0, 0)  # Off

    while True:
        set_color_logic(1, 0, 0)  # Red
        time.sleep(1)
        set_color_logic(0, 1, 0)  # Green
        time.sleep(1)
        set_color_logic(0, 0, 1)  # Blue
        time.sleep(1)
        set_color_logic(0, 0, 0)  # Off
        time.sleep(1)

except KeyboardInterrupt:
    pass

GPIO.cleanup()
