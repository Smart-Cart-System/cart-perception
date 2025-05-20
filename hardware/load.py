import time
import sys
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

hx = HX711(5, 6)

# Sensitivity settings
SENSITIVITY_THRESHOLD = 10  # Minimum weight change to trigger update (grams)
last_weight = 0  # Stores the last valid weight reading
total_weight = 0  # Stores the total weight

# Function to filter small fluctuations and ensure weight is not less than 0
def get_filtered_weight():
    global last_weight
    rawBytes = hx.getRawBytes()
    weightValue = hx.rawBytesToWeight(rawBytes)
    
    if weightValue < 0:
        weightValue = 0

    if abs(weightValue - last_weight) >= SENSITIVITY_THRESHOLD:
        last_weight = weightValue  # Update the last weight
        return weightValue
    return last_weight

# Function to wait until the weight stabilizes
def wait_for_stable_weight():
    stable_weight = get_filtered_weight()
    stable_time = time.time()
    
    while True:
        current_weight = get_filtered_weight()
        if current_weight == stable_weight:
            if time.time() - stable_time >= 1:
                return stable_weight
        else:
            stable_weight = current_weight
            stable_time = time.time()
        time.sleep(0.1)  # Add a small sleep to reduce CPU usage

# Function to get the difference between the current stable weight and the last stable weight
def get_weight_difference():
    global total_weight
    current_stable_weight = wait_for_stable_weight()
    weight_difference = current_stable_weight - total_weight
    total_weight = current_stable_weight
    return weight_difference

hx.setReadingFormat("MSB", "MSB")

print("[INFO] Automatically setting the offset.")
hx.autosetOffset()
offsetValue = hx.getOffset()
print(f"[INFO] Finished automatically setting the offset. The new value is '{offsetValue}'.")

print("[INFO] You can add weight now!")

referenceUnit = 216  # Adjust based on your scale
hx.setReferenceUnit(referenceUnit)
print(f"[INFO] Finished setting the 'referenceUnit' at {referenceUnit}.")

while True:
    try:
        weight_difference = get_weight_difference()
        if weight_difference != 0:
            print(f"Weight difference: {weight_difference:.2f} grams")
        time.sleep(1)  # Increase sleep interval to reduce CPU usage
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] 'KeyboardInterrupt Exception' detected. Cleaning and exiting...")
        sys.exit()