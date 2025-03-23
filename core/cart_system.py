import cv2
import time
import RPi.GPIO as GPIO

from hardware.camera import set_camera_properties
from utils.barcode_detection import detect_barcode
from api.api_interaction import CartAPI
from hardware.weight_tracking import WeightTracker
from utils.cart_inventory import CartInventory
from hardware.buzzer import BuzzerUtil
from core.cart_state import CartState
from core.config import DEFAULT_FOCUS_VALUE, WEIGHT_CHECK_INTERVAL, NOISE_THRESHOLD, CART_SUMMARY_INTERVAL
from handlers.barcode_handlers import BarcodeHandlers
from handlers.weight_handlers import WeightHandlers

class CartSystem:
    """Main class for the cart perception system, manages barcode detection and weight tracking."""

    def __init__(self, cart_id=1):
        """Initialize the cart system with all necessary components."""
        # Initialize hardware
        self.cap = self._init_camera()
        self.focus_value = DEFAULT_FOCUS_VALUE
        self.buzzer = BuzzerUtil()

        # Initialize tracking components
        self.weight_tracker = WeightTracker()
        self.cart = CartInventory()
        self.api = CartAPI(cart_id=cart_id)

        # State management
        self.state = CartState.NORMAL
        self.unscanned_weight = 0
        self.removal_candidates = []
        self.removal_weight_diff = 0
        self.expected_weight_before_removal = 0

        # Timing variables
        self.last_weight_check = time.time()
        self.last_cart_summary = time.time()

    def _init_camera(self):
        """Initialize and configure camera."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera.")
        set_camera_properties(cap)
        return cap

    def run(self):
        """Main loop for running the cart system."""
        print("[INFO] System ready! Scan items and add/remove them from the cart.")
        self.buzzer.item_added()
        
        try:
            while True:
                # Process camera frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame.")
                    break
                
                # Detect barcode and process state
                self._process_barcode(detect_barcode(frame))
                
                # Check weight changes
                current_time = time.time()
                self._check_weight_changes(current_time)
                self._update_cart_summary(current_time)
                
                # Handle user input
                if self._handle_keyboard_input():
                    break  # Exit if needed
                    
        except Exception as e:
            self.buzzer.error_occurred()
            print(f"[ERROR] An unexpected error occurred: {e}")
        
        finally:
            self._cleanup()

    def _process_barcode(self, barcode_number):
        """Process detected barcode based on current system state."""
        if not barcode_number:
            return
            
        # Play scan sound if new barcode
        if barcode_number != self.cart.last_scanned_barcode:
            self.buzzer.item_scanned()
            
        # Handle barcode based on current state
        if self.state == CartState.WAITING_FOR_SCAN:
            BarcodeHandlers.handle_during_scan_wait(self, barcode_number)
        elif self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            BarcodeHandlers.handle_during_removal_wait(self, barcode_number)
        else:  # NORMAL state
            BarcodeHandlers.handle_normal(self, barcode_number)

    def _check_weight_changes(self, current_time):
        """Check for weight changes and update system state accordingly."""
        if current_time - self.last_weight_check < WEIGHT_CHECK_INTERVAL:
            return
            
        self.last_weight_check = current_time
        current_actual_weight = self.weight_tracker.get_current_weight()
        
        # Check for special case: item put back during removal wait
        if self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            WeightHandlers.check_item_returned(self, current_actual_weight)
            return  # Skip normal weight processing when waiting for removal scan
            
        weight_diff = self.weight_tracker.get_weight_change()
        
        # Process significant weight changes
        if abs(weight_diff) > NOISE_THRESHOLD:
            print(f"Weight change detected: {weight_diff:.2f}g")
            
            if weight_diff > 0:
                WeightHandlers.handle_weight_increase(self, weight_diff)
            else:
                WeightHandlers.handle_weight_decrease(self, weight_diff, current_actual_weight)
        elif self.state == CartState.WAITING_FOR_SCAN:
            WeightHandlers.check_weight_normalized(self, current_actual_weight)

    def _update_cart_summary(self, current_time):
        """Update and display cart summary periodically."""
        if current_time - self.last_cart_summary < CART_SUMMARY_INTERVAL:
            return
            
        self.last_cart_summary = current_time
        print("\n" + self.cart.get_cart_summary() + "\n")
        
        if self.state == CartState.WAITING_FOR_SCAN:
            print("⚠️ Please scan the barcode for the recently added item!")
        elif self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            print("⚠️ Please scan the barcode of the removed item!")
            print(f"Possible items: {[b for b, _ in self.removal_candidates]}")

    def _handle_keyboard_input(self):
        """Handle keyboard input, returns True if program should exit."""
        cv2.imshow("Cart Camera", self.cap.read()[1])
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return True
        elif key == ord('t'):
            self.focus_value += 10
            self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value)
            print("focus:", self.focus_value)
        elif key == ord('y'):
            self.focus_value -= 10
            self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value)
            print("focus:", self.focus_value)
        elif key == ord('c'):
            # Clear the cart manually
            self._reset_cart()
        elif key == ord('r') and self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            # Cancel removal scan wait state
            print("Removal scan cancelled by user")
            self.api.cancel_warning()
            self.state = CartState.NORMAL
            self.removal_candidates = []
            
        return False

    def _reset_cart(self):
        """Reset cart and weight tracking."""
        self.cart.clear_cart()
        self.weight_tracker.reset()
        self.state = CartState.NORMAL
        self.unscanned_weight = 0
        self.removal_candidates = []
        print("Cart and weight tracking reset")

    def _cleanup(self):
        """Clean up resources before exiting."""
        self.buzzer.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()
        try:
            self.weight_tracker.cleanup()
        except:
            GPIO.cleanup()
