import RPi.GPIO as GPIO
import time
import threading

class LEDController:
    """LED Controller with PWM support for RGB LED control."""
    
    def __init__(self, red_pin=17, green_pin=27, blue_pin=22, pwm_frequency=1000):
        """Initialize LED controller with PWM support.
        
        Args:
            red_pin (int): GPIO pin for red LED
            green_pin (int): GPIO pin for green LED  
            blue_pin (int): GPIO pin for blue LED
            pwm_frequency (int): PWM frequency in Hz
        """
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.pwm_frequency = pwm_frequency
        
        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        
        # Initialize PWM
        self.red_pwm = GPIO.PWM(self.red_pin, self.pwm_frequency)
        self.green_pwm = GPIO.PWM(self.green_pin, self.pwm_frequency)
        self.blue_pwm = GPIO.PWM(self.blue_pin, self.pwm_frequency)
        
        # Start PWM with 0 duty cycle (LED off)
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
        
        # Animation control
        self.animation_running = False
        self.animation_thread = None
        self.stop_animation = False
        
        print("[INFO] LED Controller initialized")
    
    def set_color_pwm(self, red_intensity, green_intensity, blue_intensity):
        """Set LED color using PWM with intensity control.
        
        Args:
            red_intensity (float): Red intensity (0-100)
            green_intensity (float): Green intensity (0-100)
            blue_intensity (float): Blue intensity (0-100)
        """
        # Invert logic: 0% = fully on (GPIO LOW), 100% = fully off (GPIO HIGH)
        red_duty = 100 - max(0, min(100, red_intensity))
        green_duty = 100 - max(0, min(100, green_intensity))
        blue_duty = 100 - max(0, min(100, blue_intensity))
        
        self.red_pwm.ChangeDutyCycle(red_duty)
        self.green_pwm.ChangeDutyCycle(green_duty)
        self.blue_pwm.ChangeDutyCycle(blue_duty)
    
    def set_color_logic(self, red, green, blue):
        """Set LED color using simple logic (0=on, 1=off).
        
        Args:
            red (int): Red state (0=on, 1=off)
            green (int): Green state (0=on, 1=off)
            blue (int): Blue state (0=on, 1=off)
        """
        # Convert logic to PWM intensity (0=100% intensity, 1=0% intensity)
        red_intensity = 0 if red == 0 else 100
        green_intensity = 0 if green == 0 else 100
        blue_intensity = 0 if blue == 0 else 100
        
        self.set_color_pwm(red_intensity, green_intensity, blue_intensity)
    
    def red(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(intensity, 0, 0)
        print(f"LED: Red (intensity: {intensity}%)")
    
    def green(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(0, intensity, 0)
        print(f"LED: Green (intensity: {intensity}%)")
    
    def blue(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(0, 0, intensity)
        print(f"LED: Blue (intensity: {intensity}%)")
    
    def yellow(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(intensity, intensity, 0)
        print(f"LED: Yellow (intensity: {intensity}%)")
    
    def orange(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(intensity, intensity * 0.5, 0)
        print(f"LED: Orange (intensity: {intensity}%)")
    
    def white(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(intensity, intensity, intensity)
        print(f"LED: White (intensity: {intensity}%)")
    
    def off(self):
        self.stop_current_animation()
        self.set_color_pwm(0, 0, 0)
        print("LED: Off")
    
    def purple(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(intensity, 0, intensity)        
        print(f"LED: Purple (intensity: {intensity}%)")
    
    def cyan(self, intensity=100):
        self.stop_current_animation()
        self.set_color_pwm(0, intensity, intensity)
        print(f"LED: Cyan (intensity: {intensity}%)")
    
    def stop_current_animation(self):
        """Stop any running animation."""
        if self.animation_running:
            self.stop_animation = True
            if self.animation_thread and self.animation_thread.is_alive() and self.animation_thread != threading.current_thread():
                try:
                    self.animation_thread.join(timeout=1.0)
                except RuntimeError:
                    # Cannot join current thread
                    pass
            self.animation_running = False
    
    def loading(self, max_intensity=100, fade_speed=0.01, duration=0):
        """Create a loading animation by fading orange color in and out continuously.
        
        Args:
            max_intensity (float): Maximum orange intensity (0-100)
            fade_speed (float): Time between fade steps in seconds (smaller is faster)
            duration (float): Duration in seconds (0 for infinite)
        """
        def loading_animation():
            try:
                self.animation_running = True
                self.stop_animation = False
                start_time = time.time()
                
                while (duration == 0 or time.time() - start_time < duration) and not self.stop_animation:
                    # Fade in
                    for intensity in range(0, int(max_intensity) + 1):
                        if self.stop_animation:
                            return
                        self.set_color_pwm(intensity, intensity * 0.5, 0)  # Orange color
                        time.sleep(fade_speed)
                    
                    # Fade out
                    for intensity in range(int(max_intensity), -1, -1):
                        if self.stop_animation:
                            return
                        self.set_color_pwm(intensity, intensity * 0.5, 0)  # Orange color
                        time.sleep(fade_speed)
            finally:
                self.animation_running = False
                if not self.stop_animation:
                    self.off()
        
        self.stop_current_animation()
        self.animation_thread = threading.Thread(target=loading_animation, name="loading_animation", daemon=True)
        self.animation_thread.start()
        return self  # Enable method chaining
    
    def pulse(self, color_func, max_intensity=100, pulse_speed=0.05, duration=3):
        """Make LED pulse with specified color.
        
        Args:
            color_func (function): Color function to call (e.g., self.red)
            max_intensity (float): Maximum intensity (0-100)
            pulse_speed (float): Speed of pulse (smaller is faster)
            duration (float): Duration in seconds (0 for infinite)
        """
        def pulse_animation():
            try:
                self.animation_running = True
                self.stop_animation = False
                start_time = time.time()
                
                while (duration == 0 or time.time() - start_time < duration) and not self.stop_animation:
                    # Pulse up
                    for intensity in range(0, int(max_intensity) + 1, 5):
                        if self.stop_animation:
                            return
                        # Use direct PWM control to avoid recursively stopping animations
                        if color_func == self.red:
                            self.set_color_pwm(intensity, 0, 0)
                        elif color_func == self.green:
                            self.set_color_pwm(0, intensity, 0)
                        elif color_func == self.blue:
                            self.set_color_pwm(0, 0, intensity)
                        elif color_func == self.yellow:
                            self.set_color_pwm(intensity, intensity, 0)
                        elif color_func == self.orange:
                            self.set_color_pwm(intensity, intensity * 0.5, 0)
                        elif color_func == self.white:
                            self.set_color_pwm(intensity, intensity, intensity)
                        elif color_func == self.purple:
                            self.set_color_pwm(intensity, 0, intensity)
                        elif color_func == self.cyan:
                            self.set_color_pwm(0, intensity, intensity)
                        time.sleep(pulse_speed)
                    
                    # Pulse down
                    for intensity in range(int(max_intensity), -1, -5):
                        if self.stop_animation:
                            return
                        # Use direct PWM control to avoid recursively stopping animations
                        if color_func == self.red:
                            self.set_color_pwm(intensity, 0, 0)
                        elif color_func == self.green:
                            self.set_color_pwm(0, intensity, 0)
                        elif color_func == self.blue:
                            self.set_color_pwm(0, 0, intensity)
                        elif color_func == self.yellow:
                            self.set_color_pwm(intensity, intensity, 0)
                        elif color_func == self.orange:
                            self.set_color_pwm(intensity, intensity * 0.5, 0)
                        elif color_func == self.white:
                            self.set_color_pwm(intensity, intensity, intensity)
                        elif color_func == self.purple:
                            self.set_color_pwm(intensity, 0, intensity)
                        elif color_func == self.cyan:
                            self.set_color_pwm(0, intensity, intensity)
                        time.sleep(pulse_speed)
            finally:
                self.animation_running = False
                if not self.stop_animation:
                    self.off()
        
        self.stop_current_animation()
        self.animation_thread = threading.Thread(target=pulse_animation, name="pulse_animation", daemon=True)
        self.animation_thread.start()
        return self  # Enable method chaining
    
    def blink(self, color_func, intensity=100, blink_count=3, blink_speed=0.5):
        """Make LED blink with specified color.
        
        Args:
            color_func (function): Color function to call (e.g., self.red)
            intensity (float): Color intensity (0-100)
            blink_count (int): Number of blinks (0 for infinite)
            blink_speed (float): Time between blinks in seconds
        """
        def blink_animation():
            try:
                self.animation_running = True
                self.stop_animation = False
                
                count = 0
                while (count < blink_count or blink_count == 0) and not self.stop_animation:
                    if self.stop_animation:
                        break
                    
                    # On - use a color setting method that doesn't try to stop animations
                    if color_func == self.red:
                        self.set_color_pwm(intensity, 0, 0)
                    elif color_func == self.green:
                        self.set_color_pwm(0, intensity, 0)
                    elif color_func == self.blue:
                        self.set_color_pwm(0, 0, intensity)
                    elif color_func == self.yellow:
                        self.set_color_pwm(intensity, intensity, 0)
                    elif color_func == self.orange:
                        self.set_color_pwm(intensity, intensity * 0.5, 0)
                    elif color_func == self.white:
                        self.set_color_pwm(intensity, intensity, intensity)
                    elif color_func == self.purple:
                        self.set_color_pwm(intensity, 0, intensity)
                    elif color_func == self.cyan:
                        self.set_color_pwm(0, intensity, intensity)
                    
                    time.sleep(blink_speed)
                    
                    if self.stop_animation:
                        break
                        
                    # Off
                    self.set_color_pwm(0, 0, 0)
                    time.sleep(blink_speed)
                    
                    count += 1
            finally:
                self.animation_running = False
                if not self.stop_animation:
                    self.off()
        
        self.stop_current_animation()
        self.animation_thread = threading.Thread(target=blink_animation, name="blink_animation", daemon=True)
        self.animation_thread.start()
        return self  # Enable method chaining
    
    def cleanup(self):
        self.stop_current_animation()
        self.off()
        self.red_pwm.stop()
        self.green_pwm.stop()
        self.blue_pwm.stop()
        print("[INFO] LED Controller cleaned up")
