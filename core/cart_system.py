import cv2
import time
import RPi.GPIO as GPIO

from hardware.camera import set_camera_properties
from utils.barcode_detection import detect_barcode
from api.api_interaction import CartAPI
from hardware.weight_tracking import WeightTracker
from utils.cart_inventory import CartInventory
from hardware.speaker import SpeakerUtil
from core.cart_state import CartState
from core.config import Config
from handlers.barcode_handlers import BarcodeHandlers
from handlers.weight_handlers import WeightHandlers
from hardware.led import LEDController

class CartSystem:
    """Main class for the cart perception system, manages barcode detection and weight tracking."""

    def __init__(self, cart_id=1):
        """Initialize the cart system with all necessary components."""
        self.speaker = SpeakerUtil()
        self.led = LEDController()

        # Initialize hardware
        self.cap1, self.cap2 = self._init_cameras()
        self.focus_value1 = Config.DEFAULT_FOCUS_VALUE
        self.focus_value2 = Config.DEFAULT_FOCUS_VALUE

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

    def _init_cameras(self):
        """Initialize and configure both cameras."""
        cap1 = cv2.VideoCapture("/dev/cam_scan_left")
        cap2 = cv2.VideoCapture("/dev/cam_scan_right")
        
        if not cap1.isOpened():
            self.speaker.camera_error()
            raise RuntimeError("Could not open camera 1.")
            
        if not cap2.isOpened():
            self.speaker.camera_error()
            cap1.release()  # Clean up first camera if second fails
            raise RuntimeError("Could not open camera 2.")
            
        set_camera_properties(cap1)
        set_camera_properties(cap2)
        return cap1, cap2

    def run(self):
        """Main loop for running the cart system."""
        print("[INFO] System ready! Scan items and add/remove them from the cart.")
        self.speaker.quack()
        self.led.pulse(self.led.green)

        try:
            while True:
                # Process frames from both cameras
                ret1, frame1 = self.cap1.read()
                ret2, frame2 = self.cap2.read()
                
                if not ret1 or not ret2:
                    print("Error: Could not read frame from one or both cameras.")
                    self.speaker.camera_error()
                    self.led.red(100)  # Red LED for camera error
                    break
                
                # Detect barcodes from both cameras and process state
                barcode1 = detect_barcode(frame1)
                barcode2 = detect_barcode(frame2)
                
                # Process barcodes from either camera (prioritize camera1 if both detect)
                detected_barcode = barcode1 if barcode1 else barcode2
                self._process_barcode(detected_barcode)
                
                # Update LED based on current state
                self._update_led_status()
                
                # Check weight changes
                current_time = time.time()
                self._check_weight_changes(current_time)
                self._update_cart_summary(current_time)
                
                # Handle user input (pass both frames for display)
                if self._handle_keyboard_input(frame1, frame2):
                    break  # Exit if needed
                    
        except Exception as e:
            self.speaker.failure()
            print(f"[ERROR] An unexpected error occurred: {e}")        
        finally:
            self._cleanup()

    def _process_barcode(self, barcode_number):
        """Process detected barcode based on current system state."""
        if not barcode_number:
            return
            
        # Play scan sound and show LED feedback if new barcode
        if barcode_number != self.cart.last_scanned_barcode:
            self.speaker.item_read()
            # Brief white flash to indicate barcode read
            self.led.white(100)
            time.sleep(0.1)
            
        # Handle barcode based on current state
        if self.state == CartState.WAITING_FOR_SCAN:
            BarcodeHandlers.handle_during_scan_wait(self, barcode_number)
        elif self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            BarcodeHandlers.handle_during_removal_wait(self, barcode_number)
        else:  # NORMAL state
            BarcodeHandlers.handle_normal(self, barcode_number)

    def _check_weight_changes(self, current_time):
        """Check for weight changes and update system state accordingly."""
        if current_time - self.last_weight_check < Config.WEIGHT_CHECK_INTERVAL:
            return
            
        self.last_weight_check = current_time
        current_actual_weight = self.weight_tracker.get_current_weight()
        
        # Check for special case: item put back during removal wait
        if self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            WeightHandlers.check_item_returned(self, current_actual_weight)
            return  # Skip normal weight processing when waiting for removal scan
            
        weight_diff = self.weight_tracker.get_weight_change()
        
        # Process significant weight changes
        if abs(weight_diff) > Config.NOISE_THRESHOLD:
            print(f"Weight change detected: {weight_diff:.2f}g")
            
            if weight_diff > 0:
                WeightHandlers.handle_weight_increase(self, weight_diff)
            else:
                WeightHandlers.handle_weight_decrease(self, weight_diff, current_actual_weight)
        elif self.state == CartState.WAITING_FOR_SCAN:
            WeightHandlers.check_weight_normalized(self, current_actual_weight)

    def _update_cart_summary(self, current_time):
        """Update and display cart summary periodically."""
        if current_time - self.last_cart_summary < Config.CART_SUMMARY_INTERVAL:
            return
            
        self.last_cart_summary = current_time
        print("\n" + self.cart.get_cart_summary() + "\n")
        
        if self.state == CartState.WAITING_FOR_SCAN:
            print("⚠️ Please scan the barcode for the recently added item!")
        elif self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            print("⚠️ Please scan the barcode of the removed item!")
            print(f"Possible items: {[b for b, _ in self.removal_candidates]}")

    def _handle_keyboard_input(self, frame1, frame2):
        """Handle keyboard input, returns True if program should exit."""
        cv2.imshow("Cart Camera 1", frame1)
        cv2.imshow("Cart Camera 2", frame2)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return True
        elif key == ord('t'):
            # Increase focus for camera 1
            self.focus_value1 += 10
            self.cap1.set(cv2.CAP_PROP_FOCUS, self.focus_value1)
            print("Camera 1 focus:", self.focus_value1)
        elif key == ord('y'):
            # Decrease focus for camera 1
            self.focus_value1 -= 10
            self.cap1.set(cv2.CAP_PROP_FOCUS, self.focus_value1)
            print("Camera 1 focus:", self.focus_value1)
        elif key == ord('u'):
            # Increase focus for camera 2
            self.focus_value2 += 10
            self.cap2.set(cv2.CAP_PROP_FOCUS, self.focus_value2)
            print("Camera 2 focus:", self.focus_value2)
        elif key == ord('i'):
            # Decrease focus for camera 2
            self.focus_value2 -= 10
            self.cap2.set(cv2.CAP_PROP_FOCUS, self.focus_value2)
            print("Camera 2 focus:", self.focus_value2)
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
    
    def _update_led_status(self):
        """Update LED color based on current cart system state."""
        if self.state == CartState.NORMAL:
            self.led.white(100)
        elif self.state == CartState.WAITING_FOR_SCAN:
            # Waiting for barcode scan - loading animation with orange
            if not self.led.animation_running:
                self.led.loading(max_intensity=90, fade_speed=0.01, duration=0)  # Continuous until state changes
        elif self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            # Waiting for removal scan - blinking orange
            if not self.led.animation_running:
                self.led.blink(self.led.orange, intensity=90, blink_count=999, blink_speed=0.3)
        
        # Additional visual feedback for unscanned weight
        if self.unscanned_weight > 0 and self.state == CartState.NORMAL:
            # Pulse blue to indicate unscanned items
            if not self.led.animation_running:
                self.led.pulse(self.led.blue, max_intensity=100, pulse_speed=0.08, duration=999)
    
    def _cleanup(self):
        """Clean up resources before exiting."""
        print("[INFO] Cleaning up resources...")
        self.speaker.cleanup()
        self.led.cleanup()
        self.cap1.release()
        self.cap2.release()
        cv2.destroyAllWindows()
        try:
            self.weight_tracker.cleanup()
        except:
            GPIO.cleanup()
