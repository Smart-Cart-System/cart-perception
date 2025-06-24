# filepath: d:\AAST\grad\codes\cart-perception\hardware\speaker.py
import os
import threading
import pygame

class SpeakerUtil:
    """Utility class for playing different sound files for cart events."""
    
    # Define the sound file paths relative to the module
    SOUND_PATHS = {
        'item_added': '../sounds/item_added.mp3',
        'item_read': '../sounds/item_read.mp3',
        'item_removed': '../sounds/item_removed.mp3',
        'camera_error': '../sounds/camera_error.mp3',
        'warning': '../sounds/warning.mp3',
        'error': '../sounds/error.mp3',
        'failure': '../sounds/failure.mp3',
        'quack': '../sounds/quack.mp3',
    }
    
    def __init__(self, sound_dir=None):
        """Initialize the speaker interface.
        
        Args:
            sound_dir (str, optional): Directory where sound files are stored.
                                      If None, uses default relative paths.
        """
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Setup sound paths
        self.sounds = {}
        self.is_busy = False
        self.stop_requested = False
        
        # If sound_dir is provided, use it as the base directory for sounds
        self.sound_dir = sound_dir
        
        # Load sounds
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all sound files into memory."""
        for sound_name, sound_path in self.SOUND_PATHS.items():
            # If sound_dir is provided, join it with the sound path
            if self.sound_dir:
                full_path = os.path.join(self.sound_dir, os.path.basename(sound_path))
            else:
                # Use the path relative to the module
                module_dir = os.path.dirname(os.path.abspath(__file__))
                full_path = os.path.join(module_dir, sound_path)
            
            # Check if the sound file exists
            if os.path.exists(full_path):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(full_path)
                except Exception as e:
                    print(f"Error loading sound {sound_name} from {full_path}: {e}")
            else:
                print(f"Warning: Sound file not found: {full_path}")
    
    def _play_sound(self, sound_name):
        """Internal method to play a sound.
        
        Args:
            sound_name (str): Name of the sound to play.
        """
        self.stop_requested = False
        self.is_busy = True
        
        if sound_name in self.sounds:
            if not self.stop_requested:
                self.sounds[sound_name].play()
                # Wait for the sound to finish playing
                while pygame.mixer.get_busy() and not self.stop_requested:
                    pygame.time.delay(100)  # Short delay to prevent high CPU usage
        else:
            print(f"Warning: Sound '{sound_name}' not found")
        
        self.is_busy = False
    
    def play_async(self, sound_name):
        """Play a sound in a separate thread.
        
        Args:
            sound_name (str): Name of the sound to play.
        """
        if self.is_busy:
            self.stop()  # Stop any currently playing sound
        
        if sound_name in self.SOUND_PATHS:
            thread = threading.Thread(target=self._play_sound, args=(sound_name,), daemon=True)
            thread.start()
        else:
            print(f"Warning: Unknown sound name: {sound_name}")
            print(f"Available sounds: {list(self.SOUND_PATHS.keys())}")
    
    def stop(self):
        """Stop any currently playing sound."""
        if self.is_busy:
            self.stop_requested = True
            pygame.mixer.stop()
    
    # Pre-defined sound methods for different events
    def item_added(self):
        """Play sound for when an item is added to cart."""
        self.play_async('item_added')
    
    def item_read(self):
        """Play sound for when an item barcode is read."""
        self.play_async('item_read')
    
    def item_removed(self):
        """Play sound for when an item is removed from cart."""
        self.play_async('item_removed')
    
    def warning(self):
        """Play sound for when a warning occurs."""
        self.play_async('warning')
    
    def camera_error(self):
        """Play sound for when a camera error occurs."""
        self.play_async('camera_error')

    def error(self):
        """Play sound for when an error occurs."""
        self.play_async('error')

    def failure(self):
        """Play sound for when a failure occurs."""
        self.play_async('failure')
    
    def quack(self):
        """Play a quack sound."""
        self.play_async('quack')

    def play_custom(self, sound_name):
        """Play a custom sound by name.
        
        Args:
            sound_name (str): Name of the sound to play.
        """
        self.play_async(sound_name)
    
    def add_sound(self, name, file_path):
        """Add a new sound to the collection.
        
        Args:
            name (str): Name to identify the sound.
            file_path (str): Path to the sound file.
        
        Returns:
            bool: True if sound was successfully added, False otherwise.
        """
        if os.path.exists(file_path):
            try:
                self.sounds[name] = pygame.mixer.Sound(file_path)
                self.SOUND_PATHS[name] = file_path
                return True
            except Exception as e:
                print(f"Error adding sound {name} from {file_path}: {e}")
                return False
        else:
            print(f"Error: Sound file not found: {file_path}")
            return False
    
    def cleanup(self):
        """Clean up resources, should be called before program exit."""
        self.stop()
        pygame.mixer.quit()