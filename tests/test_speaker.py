import sys
import os
import time

# Add the parent directory to the path so we can import from hardware
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.speaker import SpeakerUtil

def test_all_sounds():
    """Test all sound paths in SpeakerUtil by playing each one with delays."""
    
    print("Starting SpeakerUtil sound test...")
    print("=" * 50)
    
    # Initialize the speaker utility
    speaker = SpeakerUtil()
    
    # Get all available sound names
    sound_names = list(speaker.SOUND_PATHS.keys())
    
    print(f"Found {len(sound_names)} sounds to test:")
    for i, sound_name in enumerate(sound_names, 1):
        print(f"{i}. {sound_name}")
    
    print("\n" + "=" * 50)
    print("Starting playback test...")
    print("=" * 50)
    
    try:
        for i, sound_name in enumerate(sound_names, 1):
            print(f"\n[{i}/{len(sound_names)}] Testing sound: '{sound_name}'")
            print("-" * 30)
            
            # Wait 2 seconds before playing
            print("Waiting 2 seconds before playing...")
            time.sleep(2)
            
            # Play the sound
            print(f"Playing '{sound_name}'...")
            speaker.play_async(sound_name)
            
            # Wait 2 seconds after playing
            print("Waiting 2 seconds after playing...")
            time.sleep(2)
            
            # Additional wait to ensure sound finishes playing
            while speaker.is_busy:
                time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user (Ctrl+C)")
    
    except Exception as e:
        print(f"\nError during testing: {e}")
    
    finally:
        print("\n" + "=" * 50)
        print("Cleaning up...")
        speaker.cleanup()
        print("SpeakerUtil test completed!")

if __name__ == "__main__":
    print("SpeakerUtil Test Suite")
    print("=" * 50)
        
    test_all_sounds()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
