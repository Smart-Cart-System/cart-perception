import cv2
import time
import sys
import RPi.GPIO as GPIO

from camera import set_camera_properties
from barcode_detection import detect_barcode
from api_interaction import send_barcode_to_server
from weight_tracking import WeightTracker
from cart_inventory import CartInventory

def main():
    """Main function to integrate barcode detection with weight tracking."""
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    set_camera_properties(cap)
    focus_value = 400
    
    try:
        # Initialize weight tracking system
        weight_tracker = WeightTracker()
        cart = CartInventory()
        
        last_weight_check = time.time()
        last_cart_summary = time.time()
        waiting_for_scan = False  # Flag to track if we're waiting for a barcode scan
        unscanned_weight = 0  # Track weight change that occurred without a barcode
        
        print("[INFO] System ready! Scan items and add/remove them from the cart.")
        
        while True:
            # Camera frame processing
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break
            
            # Detect barcode
            barcode_number = detect_barcode(frame)
            
            # Handle barcode detection
            if barcode_number:
                if waiting_for_scan:
                    print(f"Barcode scanned after weight change: {barcode_number}")
                    cart.add_item(barcode_number, unscanned_weight)
                    waiting_for_scan = False
                    unscanned_weight = 0
                elif barcode_number != cart.last_scanned_barcode:
                    print(f"New barcode detected: {barcode_number}")
                    send_barcode_to_server(barcode_number, "cart123", 1)
                    cart.set_pending_barcode(barcode_number)
            
            # Check weight changes periodically
            current_time = time.time()
            if current_time - last_weight_check >= 1.0:
                # Get current weight and the difference
                current_actual_weight = weight_tracker.get_current_weight()
                weight_diff = weight_tracker.get_weight_change()
                
                # Process significant weight changes
                if abs(weight_diff) > 5:  # 5 gram threshold for noise
                    print(f"Weight change detected: {weight_diff:.2f}g")
                    
                    # Case 1: Weight increase with pending barcode (adding product)
                    if weight_diff > 0 and cart.pending_weight_change and cart.last_scanned_barcode:
                        cart.add_item(cart.last_scanned_barcode, weight_diff)
                    
                    # Case 2: Weight increase without pending barcode (unknown addition)
                    elif weight_diff > 0:
                        # Check if we're already waiting for a scan
                        if waiting_for_scan:
                            # Add to the unscanned weight
                            unscanned_weight += weight_diff
                        else:
                            # Start waiting for scan
                            waiting_for_scan = True
                            unscanned_weight = weight_diff
                        
                        # Prompt user to scan barcode
                        print(f"WARNING: Item added without scanning barcode. Weight: {unscanned_weight:.2f}g")
                        print("Please scan the barcode of the added item!")
                    
                    # Case 3: Weight decrease (item removal)
                    elif weight_diff < 0:
                        # If we were waiting for a scan, cancel it if weight returns to normal
                        if waiting_for_scan:
                            # Check if weight is back to expected (within tolerance)
                            expected_weight = cart.total_expected_weight
                            if abs(current_actual_weight - expected_weight) < 10:  # 10g tolerance
                                print("Weight returned to normal, cancelling scan request")
                                waiting_for_scan = False
                                unscanned_weight = 0
                        else:
                            # Normal item removal process
                            matches = cart.find_removed_item(weight_diff)
                            
                            if len(matches) == 1:
                                barcode, item_data = matches[0]
                                print(f"Removed item: {barcode}, weight: {item_data['weight']:.2f}g")
                                cart.remove_item(barcode)
                            elif len(matches) > 1:
                                print(f"Ambiguous removal: {len(matches)} items match the weight {abs(weight_diff):.2f}g")
                                print("Possible matches:", [b for b, _ in matches])
                            else:
                                print(f"Unknown item removed with weight {abs(weight_diff):.2f}g")
                
                # Check if weight has returned to expected value while waiting for scan
                elif waiting_for_scan:
                    expected_weight = cart.total_expected_weight
                    if abs(current_actual_weight - expected_weight) < 10:  # 10g tolerance
                        print("Weight returned to normal, cancelling scan request")
                        waiting_for_scan = False
                        unscanned_weight = 0
                
                last_weight_check = current_time
            
            # Display cart summary periodically
            if current_time - last_cart_summary >= 10.0:
                print("\n" + cart.get_cart_summary() + "\n")
                if waiting_for_scan:
                    print("⚠️ Please scan the barcode for the recently added item!")
                last_cart_summary = current_time
            
            # Display camera preview
            cv2.imshow('Camera Preview', frame)
            
            # Status overlay
            status_img = frame.copy()
            if waiting_for_scan:
                cv2.putText(status_img, "PLEASE SCAN BARCODE", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(status_img, f"Unscanned Weight: {unscanned_weight:.1f}g", (50, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow('Camera Preview', status_img)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('t'):
                focus_value += 10
                cap.set(cv2.CAP_PROP_FOCUS, focus_value)
                print("focus:", focus_value)
            elif key == ord('y'):
                focus_value -= 10
                cap.set(cv2.CAP_PROP_FOCUS, focus_value)
                print("focus:", focus_value)
            elif key == ord('c'):
                # Clear the cart manually
                cart.clear_cart()
                weight_tracker.reset()
                waiting_for_scan = False
                unscanned_weight = 0
                print("Cart and weight tracking reset")
    
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        try:
            weight_tracker.cleanup()
        except:
            GPIO.cleanup()

if __name__ == "__main__":
    main()