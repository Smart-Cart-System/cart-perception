import time
import sys
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

# Load cell configuration
DT_PIN = 19
SCK_PIN = 6
REFERENCE_UNIT = 200
update_interval = 0.5

def initialize_load_cell():
    """Initialize the HX711 load cell."""
    try:
        print("[INFO] Initializing load cell...")
        print(f"[INFO] DT Pin: {DT_PIN}, SCK Pin: {SCK_PIN}")
        print(f"[INFO] Reference Unit: {REFERENCE_UNIT}")
        
        # Create HX711 instance
        hx = HX711(DT_PIN, SCK_PIN)
        
        # Set reading format
        hx.setReadingFormat("MSB", "MSB")
        
        # Auto-set offset (tare the scale)
        print("[INFO] Setting offset (taring scale)...")
        hx.autosetOffset()
        offset = hx.getOffset()
        print(f"[INFO] Offset set to: {offset}")
        
        # Set reference unit
        hx.setReferenceUnit(REFERENCE_UNIT)
        print(f"[INFO] Reference unit set to: {REFERENCE_UNIT}")
        
        print("[INFO] Load cell initialization complete!")
        print("[INFO] You can place weight on the scale now!")
        
        return hx
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize load cell: {e}")
        return None

def get_weight(hx):
    """Get current weight reading."""
    try:
        weight = hx.getWeight()
        # Ensure weight is not negative
        return max(0, weight)
    except Exception as e:
        print(f"[ERROR] Failed to read weight: {e}")
        return 0

def main():
    """Main monitoring function."""
    print("=== Single Load Cell Total Weight Monitor ===")
    
    # Initialize load cell
    hx = initialize_load_cell()
    if not hx:
        print("[ERROR] Failed to initialize load cell. Exiting.")
        return
    
    print("\n=== Weight Monitoring Started ===")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            # Get current weight
            current_weight = get_weight(hx)
            
            # Get current time
            current_time = time.strftime("%H:%M:%S")
            
            # Print current weight (overwrite previous line)
            print(f"\r[{current_time}] Total Weight: {current_weight:8.1f}g    ", end="", flush=True)
            
            # Wait before next reading
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        print("\n[INFO] Weight monitoring stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
    finally:
        # Clean up GPIO
        GPIO.cleanup()
        print("[INFO] GPIO cleanup complete")
        print("[INFO] Weight monitoring complete!")

if __name__ == "__main__":
    main()