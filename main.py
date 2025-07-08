import sys
import asyncio
import signal
import RPi.GPIO as GPIO
import logging
from core.cart_system import CartSystem
from core.config import Config
from hardware.led import LEDController
from api.cart_websocket import CartWebSocket
from enum import Enum, auto
import time

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

class IdleState(Enum):
    """Enum representing states of the idle cart system."""
    IDLE = auto()
    QR_DISPLAY = auto()
    SESSION_ACTIVE = auto()
    PAYMENT_PROCESSING = auto()

async def main():
    """Main entry point for the cart perception system with WebSocket integration."""
    try:
        # Get cart ID from config
        cart_id = Config.CART_ID
        if not cart_id:
            logger.error("Cart ID not configured! Please set CART_ID in environment or .env file.")
            return
        
        logger.info(f"Starting cart system for cart ID: {cart_id}")
        
        # Initialize LED controller
        led_controller = LEDController()
        
        # Initialize but don't start cart system yet
        cart_system = CartSystem(cart_id=int(cart_id))
        
        # Initialize WebSocket client
        websocket_client = CartWebSocket(
            cart_id=cart_id,
            cart_system=cart_system,
            led_controller=led_controller
        )
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            logger.info("Shutdown signal received, cleaning up...")
            asyncio.create_task(shutdown(websocket_client, cart_system, led_controller))
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        # Initial state - cart is idle, only LED is off
        logger.info("System initialized and ready. Setting to IDLE state.")
        led_controller.turn_off()
        
        # Connect to WebSocket server and start listening for commands
        await websocket_client.connect()
        
    except Exception as e:
        logger.error(f"[CRITICAL ERROR] {e}")
        GPIO.cleanup()

async def shutdown(websocket_client, cart_system, led_controller):
    """Clean shutdown of all components."""
    logger.info("Shutting down cart system...")
    
    # Close WebSocket connection
    if websocket_client:
        await websocket_client.close()
    
    # Shutdown cart system
    if cart_system:
        cart_system._cleanup()
    
    # Turn off LED
    if led_controller:
        led_controller.turn_off()
    
    # Cleanup GPIO
    GPIO.cleanup()
    
    # Exit program
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user. Cleaning up...")
        GPIO.cleanup()
    except Exception as e:
        print(f"Fatal error: {e}")
        GPIO.cleanup()