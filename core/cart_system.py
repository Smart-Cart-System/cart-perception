import cv2
import time
import RPi.GPIO as GPIO
import threading

from hardware.camera import set_camera_properties, calculate_focus_measure
from utils.barcode_detection import detect_barcode
from utils.threaded_camera import ThreadedCamera
from api.api_interaction import CartAPI
from hardware.weight_tracking import WeightTracker
from utils.cart_inventory import CartInventory
from hardware.speaker import SpeakerUtil
from core.cart_state import CartState
from core.config import Config
from handlers.barcode_handlers import BarcodeHandlers
from handlers.weight_handlers import WeightHandlers
from hardware.led import LEDController
from hardware.apriltag_camera import ThreadedAprilTagCamera

class CartSystem:
    """Main class for the cart perception system, manages barcode detection and weight tracking."""

    def __init__(self, cart_id=1):
        """Initialize the cart system with all necessary components."""
        self.speaker = SpeakerUtil()
        self.led = LEDController()

        # Initialize hardware
        self._init_cameras()
        self.focus_value1 = Config.DEFAULT_FOCUS_VALUE
        self.focus_value2 = Config.DEFAULT_FOCUS_VALUE
        
        # Initialize AprilTag camera
        try:
            self.apriltag_camera = ThreadedAprilTagCamera(camera_id="/dev/cam_navigation").start()
            self.last_location_update = 0
            self.location_update_interval = 2.0  # Update location every 2 seconds
            self.last_tag_id = None
            print("[INFO] AprilTag camera initialized successfully")
        except Exception as e:
            print(f"[WARNING] Could not initialize AprilTag camera: {e}")
            self.apriltag_camera = None
        
        # Autofocus management
        self.last_af_trigger_time1 = 0
        self.last_af_trigger_time2 = 0
        self.FOCUS_THRESHOLD = 350  # Lower = allows more blur
        self.AF_RETRY_DELAY = 1.5   # seconds before retrying autofocus

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
        self.last_fps_print = time.time()
        self.frame_count = 0
        self.last_scan_time = 0

        # Add LED action tracking
        self.led_action = None
        self.led_action_start_time = 0
        self.led_action_duration = 3  # Duration in seconds for action-specific LED effects

    def _init_cameras(self):
        """Initialize and configure both cameras."""
        # Use ThreadedCamera for improved performance
        self.camera1 = ThreadedCamera("/dev/cam_scan_left", "Camera 1")
        self.camera2 = ThreadedCamera("/dev/cam_scan_right", "Camera 2")

        if not self.camera1.isOpened() or not self.camera2.isOpened():
            self.speaker.camera_error()
            raise RuntimeError("Could not open one or both cameras.")

        # Cameras are configured in the ThreadedCamera class now
        return self.camera1, self.camera2

    def run(self):
        """Main loop for running the cart system."""
        print("[INFO] System ready! Scan items and add/remove them from the cart.")
        self.speaker.quack()
        
        # Set startup LED effect
        self.led_action = "start"
        self.led_action_start_time = time.time()
        
        try:
            while True:
                # Get the current time once per loop
                current_time = time.time()
                
                # Process frames from both cameras
                frame1 = self.camera1.read()
                frame2 = self.camera2.read()
                
                if frame1 is None or frame2 is None:
                    print("[WARNING] Could not read frames")
                    continue
                
                # Process each camera frame
                processed_frame1, barcode1 = self._process_camera_frame(frame1, self.camera1, 1)
                processed_frame2, barcode2 = self._process_camera_frame(frame2, self.camera2, 2)
                
                # Process detected barcodes
                self._process_barcode(barcode1)
                self._process_barcode(barcode2)
                
                # Check for weight changes
                self._check_weight_changes(current_time)
                
                # Update cart summary
                self._update_cart_summary(current_time)
                
                # Update cart location using AprilTag
                self._update_cart_location(current_time)
                
                # Update LED status
                self._update_led_status()
                
                # Handle keyboard input
                if self._handle_keyboard_input(processed_frame1, processed_frame2):
                    break
                    
        except Exception as e:
            self.speaker.failure()
            print(f"[ERROR] An unexpected error occurred: {e}")
        finally:
            self._cleanup()

    def _process_camera_frame(self, frame, camera, camera_num):
        """Process a single camera frame for autofocus and barcode detection."""
        # Manage autofocus
        self._manage_camera_autofocus(frame, camera.cap, camera_num)
        
        # Detect barcode
        barcode = detect_barcode(frame)
        
        return frame, barcode

    def _manage_camera_autofocus(self, frame, cap, camera_num):
        """Manage autofocus for a single camera based on image sharpness."""
        current_time = time.time()
        
        # Calculate focus measure
        focus_measure = calculate_focus_measure(frame)
        
        # Debug: Add focus measure to frame
        cv2.putText(frame, f"Focus: {focus_measure:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        last_af_trigger_time = self.last_af_trigger_time1 if camera_num == 1 else self.last_af_trigger_time2

        # Autofocus logic
        if (current_time - last_af_trigger_time) > self.AF_RETRY_DELAY:
            if focus_measure < self.FOCUS_THRESHOLD:
                print(f"Camera {camera_num} focus blurry ({focus_measure:.2f}), retrying autofocus...")
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                time.sleep(0.05)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                if camera_num == 1:
                    self.last_af_trigger_time1 = current_time
                else:
                    self.last_af_trigger_time2 = current_time

    def _process_barcode(self, barcode_number):
        """Process detected barcode based on current system state."""
        if not barcode_number:
            return
            
        # Play scan sound and show LED feedback if new barcode
        if barcode_number != self.cart.last_scanned_barcode:
            self.speaker.item_read()
            # Set LED feedback for successful scan
            self.led_action = "scan"
            self.led_action_start_time = time.time()
            self.last_scan_time = time.time()
            
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

        # Check for scan timeout
        self._check_scan_timeout(current_time)
        
        # Check for special case: item put back during removal wait
        if self.state == CartState.WAITING_FOR_REMOVAL_SCAN:
            WeightHandlers.check_item_returned(self, current_actual_weight)
            return  # Skip normal weight processing when waiting for removal scan
            
        weight_diff = self.weight_tracker.get_weight_change()
        
        # Process significant weight changes
        if abs(weight_diff) > Config.NOISE_THRESHOLD:
            print(f"Weight change detected: {weight_diff:.2f}g")
            
            if weight_diff > 0:
                # Item added - set LED action
                self.led_action = "add"
                self.led_action_start_time = time.time()
                WeightHandlers.handle_weight_increase(self, weight_diff)
            else:
                # Item removed - set LED action
                self.led_action = "remove"
                self.led_action_start_time = time.time()
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

    def _check_scan_timeout(self, current_time):
        """Checks if the last scanned item should be cancelled due to a timeout."""
        if self.cart.last_scanned_barcode and (self.state == CartState.NORMAL) and (current_time - self.last_scan_time > 5.0):
            print(f"[INFO] Timeout for barcode {self.cart.last_scanned_barcode}. Cancelling scan.")
            self.cart.last_scanned_barcode = None
            self.last_scan_time = 0  # Reset timer
            self.speaker.error()  # Notify user

    def _handle_keyboard_input(self, frame1, frame2):
        """Handle keyboard input, returns True if program should exit."""
        # Combine frames for display
        combined_frame = cv2.hconcat([frame1, frame2])
        # cv2.imshow("Cart Cameras", combined_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return True
        elif key == ord('t'):
            # Increase focus for camera 1
            self.focus_value1 += 10
            self.camera1.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value1)
            print("Camera 1 focus:", self.focus_value1)
        elif key == ord('y'):
            # Decrease focus for camera 1
            self.focus_value1 -= 10
            self.camera1.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value1)
            print("Camera 1 focus:", self.focus_value1)
        elif key == ord('u'):
            # Increase focus for camera 2
            self.focus_value2 += 10
            self.camera2.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value2)
            print("Camera 2 focus:", self.focus_value2)
        elif key == ord('i'):
            # Decrease focus for camera 2
            self.focus_value2 -= 10
            self.camera2.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value2)
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
        """Update LED color based on current cart system state or recent actions."""
        current_time = time.time()
        
        # Check if we have an active LED action effect
        if self.led_action and (current_time - self.led_action_start_time < self.led_action_duration):
            # Action-specific LED effects take priority
            if self.led_action == "scan":
                # Green flash for successful scan
                if not self.led.animation_running:
                    self.led.blue(100)
            elif self.led_action == "add":
                # Blue pulse for item added
                if not self.led.animation_running:
                    self.led.green(100)
            elif self.led_action == "remove":
                # Yellow pulse for item removed
                if not self.led.animation_running:
                    self.led.yellow(100)
            elif self.led_action == "location":
                # Purple flash for location update
                if not self.led.animation_running:
                    self.led.purple(100)
            elif self.led_action == "start":
                # Green pulse for system startup
                if not self.led.animation_running:
                    self.led.green(100)
            return
        
        # Reset action if duration expired
        if self.led_action and (current_time - self.led_action_start_time >= self.led_action_duration):
            self.led_action = None
        
        # Default state-based LED behavior
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

    def _update_cart_location(self, current_time):
        """Update cart location based on AprilTag detection"""
        if not self.apriltag_camera or (current_time - self.last_location_update < self.location_update_interval):
            return
            
        self.last_location_update = current_time
        tag_id = self.apriltag_camera.get_latest_tag()
        
        if tag_id is not None and tag_id != self.last_tag_id:
            print(f"[INFO] New location detected: Aisle {tag_id}")
            response = self.api.update_session_location(tag_id)
            if response:
                self.last_tag_id = tag_id
                # Flash LED to indicate successful location update
                self.led_action = "location"
                self.led_action_start_time = current_time

    def _cleanup(self):
        """Clean up resources before exiting."""
        print("[INFO] Cleaning up resources...")
        self.speaker.cleanup()
        self.led.cleanup()
        self.camera1.release()
        self.camera2.release()
        if self.apriltag_camera:
            self.apriltag_camera.release()
        cv2.destroyAllWindows()
        try:
            self.weight_tracker.cleanup()
        except:
            GPIO.cleanup()
