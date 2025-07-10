import asyncio
import websockets
import json
import time
import logging
from core.config import Config
from core.cart_state import CartState
import ssl
import threading

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CartWebSocket')

class CartWebSocket:
    """WebSocket client for cart hardware that handles server commands and auto reconnection"""
    
    def __init__(self, cart_id, cart_system=None, led_controller=None):
        """Initialize the WebSocket client with cart ID and optional system controllers"""
        self.cart_id = cart_id
        self.server_url = Config.WEBSOCKET_SERVER_URL
        self.cart_system = cart_system
        self.led_controller = led_controller
        self.websocket = None
        self.connected = False
        self.reconnect_interval = 5  # Initial reconnect interval in seconds
        self.max_reconnect_interval = 60  # Maximum reconnect interval in seconds
        self.session_id = None
        self.running = True
        self.QR_ACTIVE_DURATION = 60  # QR active for 1 minute (in seconds)
        
        # SSL/TLS context configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification for development
    
    async def connect(self):
        """Connect to the WebSocket server with auto-reconnect functionality"""
        connection_attempt = 0
        ssl_error_count = 0
        
        while self.running:
            try:
                logger.info(f"Connecting to {self.server_url}")
                connection_attempt += 1
                
                # Connection options
                connect_kwargs = {}
                
                # Add SSL context for secure connections
                if self.server_url.startswith('wss://'):
                    connect_kwargs['ssl'] = self.ssl_context
                
                async with websockets.connect(
                    self.server_url,
                    **connect_kwargs
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    logger.info("Connected to WebSocket server")
                    self.reconnect_interval = 5  # Reset reconnect interval on successful connection
                    ssl_error_count = 0  # Reset SSL error count
                    await self._handle_messages()
                    
            except ssl.SSLError as e:
                self.connected = False
                ssl_error_count += 1
                logger.error(f"SSL error: {str(e)}")
                
                # If we get multiple SSL errors, try switching to non-secure connection
                if ssl_error_count >= 2 and self.server_url.startswith('wss://'):
                    logger.warning("Multiple SSL errors. Trying non-secure WebSocket connection...")
                    self.server_url = self.server_url.replace('wss://', 'ws://')
                    logger.info(f"Switched to non-secure URL: {self.server_url}")
                    ssl_error_count = 0  # Reset the counter
                    await asyncio.sleep(2)  # Short delay before retry
                else:
                    await asyncio.sleep(self.reconnect_interval)
                    
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.WebSocketException,
                    ConnectionRefusedError) as e:
                self.connected = False
                logger.error(f"WebSocket connection error: {str(e)}")
                
                # If we get multiple connection errors with wss://, try switching to ws://
                if connection_attempt >= 3 and self.server_url.startswith('wss://'):
                    logger.warning("Multiple connection failures. Trying non-secure WebSocket connection...")
                    self.server_url = self.server_url.replace('wss://', 'ws://')
                    logger.info(f"Switched to non-secure URL: {self.server_url}")
                    connection_attempt = 0  # Reset the counter
                
                logger.info(f"Reconnecting in {self.reconnect_interval} seconds...")
                await asyncio.sleep(self.reconnect_interval)
                # Exponential backoff with maximum limit
                self.reconnect_interval = min(self.reconnect_interval * 1.5, self.max_reconnect_interval)
                
            except Exception as e:
                self.connected = False
                logger.error(f"Unexpected error: {str(e)}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        while self.connected:
            try:
                message = await self.websocket.recv()
                logger.info(f"Received: {message}")
                
                # Parse the message
                try:
                    data = json.loads(message)
                    await self._process_command(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                    
            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                logger.warning("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
    
    async def _process_command(self, data):
        """Process commands received from the server"""
        if not isinstance(data, dict) or 'type' not in data:
            logger.error(f"Invalid command format: {data}")
            return
        
        command_type = data.get('type')
        command_data = data.get('data')
        
        logger.info(f"Processing command: {command_type}, data: {command_data}")
        
        if command_type == "generate_qr":
            await self._handle_generate_qr()
        elif command_type == "session_started":
            await self._handle_session_started(command_data)
        elif command_type == "payment_created":
            await self._handle_payment_created(command_data)
        elif command_type == "end_session":
            await self._handle_end_session(command_data)
        else:
            logger.warning(f"Unknown command type: {command_type}")
    
    async def _handle_generate_qr(self):
        """Handle generate_qr command"""
        logger.info("Preparing cart for QR code display")
        
        # if self.led_controller:
        #     self.led_controller.pulse(self.led_controller.white, pulse_speed=0.06 ,duration=self.QR_ACTIVE_DURATION)
        # List all currently active threads
        threads = threading.enumerate()

        # Print thread information
        for thread in threads:
            print(f"Name: {thread.name}, ID: {thread.ident}, Alive: {thread.is_alive()}, Daemon: {thread.daemon}")


    async def _handle_session_started(self, session_id):
        """Handle session_started command"""
        logger.info(f"Starting new session with ID: {session_id}")
        
        # Store the session ID
        self.session_id = session_id
        
        # Set session ID in the API
        if self.cart_system and hasattr(self.cart_system, 'api'):
            self.cart_system.api.session_id = session_id
            logger.info(f"API session ID set to {session_id}")
        
        # Stop any running LED animations
        # if self.led_controller:
        #     self.led_controller.stop_current_animation()

        # Start the cart system
        if self.cart_system:
            await self._start_cart_system()

        # List all currently active threads
        threads = threading.enumerate()

        # Print thread information
        for thread in threads:
            print(f"Name: {thread.name}, ID: {thread.ident}, Alive: {thread.is_alive()}, Daemon: {thread.daemon}")


    async def _handle_payment_created(self, payment_id):
        """Handle payment_created command"""
        logger.info(f"Payment created with ID: {payment_id}")
        
        if self.cart_system:
            # Disable add/remove item functionality
            self.cart_system.disable_item_operations()
            
            # Set system to monitor for fraud
            self.cart_system.enable_fraud_monitoring()
            
            # Set LED to loading animation
            # if self.led_controller:
            #     self.led_controller.stop_current_animation()
            #     self.led_controller.start_loading_animation()
    
        # List all currently active threads
        threads = threading.enumerate()

        # Print thread information
        for thread in threads:
            print(f"Name: {thread.name}, ID: {thread.ident}, Alive: {thread.is_alive()}, Daemon: {thread.daemon}")


    async def _handle_end_session(self, session_id):
        """Handle end_session command"""
        logger.info(f"Ending session with ID: {session_id}")
        
        # Turn off LED
        # if self.led_controller:
        #     self.led_controller.stop_current_animation()
        #     self.led_controller.turn_off()
        # Shutdown cart system
        if self.cart_system:
            await self._shutdown_cart_system()
        
        self.session_id = None

        # List all currently active threads
        threads = threading.enumerate()

        # Print thread information
        for thread in threads:
            print(f"Name: {thread.name}, ID: {thread.ident}, Alive: {thread.is_alive()}, Daemon: {thread.daemon}")


    async def _start_cart_system(self):
        """Start the cart system"""
        if hasattr(self.cart_system, 'start'):
            # Run cart system start method - now runs in its own thread
            self.cart_system.start()
            logger.info("Cart system started in background thread")
        else:
            logger.warning("Cart system doesn't have a start method")
    
    async def _shutdown_cart_system(self):
        """Shutdown the cart system"""
        if hasattr(self.cart_system, 'shutdown'):
            # Run cart system shutdown method
            self.cart_system.shutdown()
        else:
            logger.warning("Cart system doesn't have a shutdown method")
    
    async def close(self):
        """Close the WebSocket connection cleanly"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        self.connected = False
