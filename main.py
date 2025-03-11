import cv2
import time
import sys
import RPi.GPIO as GPIO

from camera import set_camera_properties
from barcode_detection import detect_barcode
from api_interaction import CartAPI, Ambigous
from weight_tracking import WeightTracker
from cart_inventory import CartInventory
from buzzer import BuzzerUtil

def main():
    """Main function to integrate barcode detection with weight tracking."""
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    set_camera_properties(cap)
    focus_value = 400
    
    # Initialize buzzer
    buzzer = BuzzerUtil()
    
    try:
        # Initialize weight tracking system
        weight_tracker = WeightTracker()
        cart = CartInventory()
        API = CartAPI(cart_id=1)
        
        last_weight_check = time.time()
        last_cart_summary = time.time()
        waiting_for_scan = False  # Flag to track if we're waiting for a barcode scan
        waiting_for_removal_scan = False  # Flag for ambiguous removal barcode scanning
        unscanned_weight = 0  # Track weight change that occurred without a barcode
        removal_candidates = []  # Store potential matches for removed item
        removal_weight_diff = 0  # Store the weight difference of the removal
        expected_weight_before_removal = 0  # Weight before removal to detect if item was put back
        
        print("[INFO] System ready! Scan items and add/remove them from the cart.")
        
        while True:
            # Camera frame processing
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break
            
            # Detect barcode
            barcode_number = detect_barcode(frame)
            current_time = time.time()
            
            # Print last barcode once if changed
            # if barcode_number and barcode_number != cart.last_scanned_barcode:
            #     print(f"Last scanned barcode: {barcode_number}")

            # Handle barcode detection
            if barcode_number and barcode_number != cart.last_scanned_barcode:
                buzzer.item_scanned()  # Play scan sound
                
            if barcode_number:
                if waiting_for_scan:
                    # Case 1: Scan after weight addition (unscanned item)
                    print(f"Barcode scanned after weight addition: {barcode_number}")
                    cart.add_item(barcode_number, unscanned_weight)
                    API.add_item_to_cart(barcode_number, unscanned_weight)
                    waiting_for_scan = False
                    unscanned_weight = 0
                    buzzer.item_added()  # Play item added sound
                elif waiting_for_removal_scan:
                    # Case 2: Scan after ambiguous item removal
                    found = False
                    for candidate_barcode, _ in removal_candidates:
                        if barcode_number == candidate_barcode:
                            print(f"Confirmed removal of item: {barcode_number}")
                            cart.remove_item(barcode_number)
                            API.remove_item_from_cart(barcode_number)
                            found = True
                            break
                    
                    if found:
                        buzzer.item_removed()  # Play item removed sound
                        waiting_for_removal_scan = False
                        removal_candidates = []
                    else:
                        buzzer.error_occurred()  # Play error sound
                        print(f"Warning: Scanned barcode {barcode_number} does not match any removal candidates")
                        print(f"Valid candidates are: {[b for b, _ in removal_candidates]}")
                        print("Please scan the correct barcode of the removed item")
                elif barcode_number != cart.last_scanned_barcode:
                    # Case 3: Normal barcode scan for addition
                    print(f"New barcode detected: {barcode_number}")
                    API.read_item(barcode_number)
                    cart.set_pending_barcode(barcode_number)
            
            # Check weight changes periodically
            if current_time - last_weight_check >= 0.5:  # Twice per second
                # Get current weight
                current_actual_weight = weight_tracker.get_current_weight()
                
                # Check if weight returned to normal during removal wait
                if waiting_for_removal_scan:
                    # Calculate tolerance based on the weight (larger items have larger tolerance)
                    tolerance = max(10, abs(removal_weight_diff) * 0.05)  # 5% or min 10g
                    
                    if abs(current_actual_weight - expected_weight_before_removal) < tolerance:
                        print("Weight returned to normal, item was likely put back")
                        print("Cancelling removal wait")
                        API.cancel_warning()
                        waiting_for_removal_scan = False
                        removal_candidates = []
                        continue  # Skip the normal weight processing
                
                # Skip normal weight processing if waiting for removal scan
                if not waiting_for_removal_scan:
                    weight_diff = weight_tracker.get_weight_change()
                    
                    # Process significant weight changes
                    if abs(weight_diff) > 5:  # 5 gram threshold for noise
                        print(f"Weight change detected: {weight_diff:.2f}g")
                        
                        # Case 1: Weight increase with pending barcode (adding product)
                        if weight_diff > 0 and cart.pending_weight_change and cart.last_scanned_barcode:
                            cart.add_item(cart.last_scanned_barcode, weight_diff)
                            API.add_item_to_cart(cart.last_scanned_barcode, weight_diff)
                            buzzer.item_added()  # Play item added sound

                        # Case 2: Weight increase without pending barcode (unknown addition)
                        elif weight_diff > 0:
                            # Check if we're already waiting for a scan
                            if waiting_for_scan:
                                # Add to the unscanned weight
                                unscanned_weight += weight_diff
                            else:
                                # Start waiting for scan
                                API.report_fraud_warning(Ambigous.ADDED)
                                buzzer.error_occurred()  # Play error sound
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
                                    API.cancel_warning()
                                    waiting_for_scan = False
                                    unscanned_weight = 0
                                    API.cancel_warning()
                            else:
                                # Normal item removal process
                                matches = cart.find_removed_item(weight_diff)
                                
                                if len(matches) == 1:
                                    barcode, item_data = matches[0]
                                    print(f"Removed item: {barcode}, weight: {item_data['weight']:.2f}g")
                                    cart.remove_item(barcode)
                                    API.remove_item_from_cart(barcode)
                                    buzzer.item_removed()  # Play item removed sound
                                elif len(matches) > 1:
                                    print(f"Ambiguous removal: {len(matches)} items match the weight {abs(weight_diff):.2f}g")
                                    print("Please scan the barcode of the removed item")
                                    print("Possible matches:", [b for b, _ in matches])
                                    
                                    # Enter waiting for removal scan state
                                    API.report_fraud_warning(Ambigous.REMOVED)
                                    waiting_for_removal_scan = True
                                    removal_candidates = matches
                                    removal_weight_diff = weight_diff
                                    expected_weight_before_removal = current_actual_weight - weight_diff
                                    buzzer.ambiguous_removal()  # Play once when entering this state
                                else:
                                    print(f"Unknown item removed with weight {abs(weight_diff):.2f}g")
                    
                    # Check if weight has returned to expected value while waiting for scan
                    elif waiting_for_scan:
                        expected_weight = cart.total_expected_weight
                        if abs(current_actual_weight - expected_weight) < 10:  # 10g tolerance
                            print("Weight returned to normal, cancelling scan request")
                            API.cancel_warning()
                            waiting_for_scan = False
                            unscanned_weight = 0
                
                last_weight_check = current_time
            
            # Display cart summary periodically
            if current_time - last_cart_summary >= 10.0:
                print("\n" + cart.get_cart_summary() + "\n")
                if waiting_for_scan:
                    print("⚠️ Please scan the barcode for the recently added item!")
                elif waiting_for_removal_scan:
                    print("⚠️ Please scan the barcode of the removed item!")
                    print(f"Possible items: {[b for b, _ in removal_candidates]}")
                last_cart_summary = current_time
            
            # Status overlay
            status_img = frame.copy()
            if waiting_for_scan:
                cv2.putText(status_img, "PLEASE SCAN ADDED ITEM", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(status_img, f"Unscanned Weight: {unscanned_weight:.1f}g", (50, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow('Camera Preview', status_img)
            elif waiting_for_removal_scan:
                cv2.putText(status_img, "PLEASE SCAN REMOVED ITEM", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                candidates_text = ", ".join([b for b, _ in removal_candidates[:3]])
                if len(removal_candidates) > 3:
                    candidates_text += "..."
                cv2.putText(status_img, f"Candidates: {candidates_text}", (50, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(status_img, "Press 'r' to cancel", (50, 130), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.imshow('Camera Preview', status_img)
            else:
                cv2.imshow('Camera Preview', frame)
            
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
                waiting_for_removal_scan = False
                unscanned_weight = 0
                removal_candidates = []
                print("Cart and weight tracking reset")
            elif key == ord('r') and waiting_for_removal_scan:
                # Cancel removal scan wait state
                print("Removal scan cancelled by user")
                API.cancel_warning()
                waiting_for_removal_scan = False
                removal_candidates = []
    
    except Exception as e:
        buzzer.error_occurred()  # Signal error with sound
        print(f"[ERROR] An unexpected error occurred: {e}")
    
    finally:
        # Cleanup
        buzzer.cleanup()  # Clean up buzzer
        cap.release()
        cv2.destroyAllWindows()
        try:
            weight_tracker.cleanup()
        except:
            GPIO.cleanup()

if __name__ == "__main__":
    main()