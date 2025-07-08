import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), os.pardir, ".env"))

@dataclass
class Config:
    """Configuration class for cart perception system"""
    
    # System timing constants
    WEIGHT_CHECK_INTERVAL: float = float(os.getenv('WEIGHT_CHECK_INTERVAL', 0.5))
    CART_SUMMARY_INTERVAL: float = float(os.getenv('CART_SUMMARY_INTERVAL', 10.0))
    
    # Weight detection settings
    NOISE_THRESHOLD: int = int(os.getenv('NOISE_THRESHOLD', 50))     # for weigt increase detection
    WEIGHT_TOLERANCE: int = int(os.getenv('WEIGHT_TOLERANCE', 20))  # for checking between weight and expected weight
    
    # Camera settings
    DEFAULT_FOCUS_VALUE: int = int(os.getenv('DEFAULT_FOCUS_VALUE', 400))
    
    # API settings
    API_HOST: str = os.getenv('API_HOST')
    API_KEY: str = os.getenv('API_KEY')

    # Hardware settings
    CART_ID: int = os.getenv('CART_ID')

    # WebSocket server URL
    WEBSOCKET_SERVER_URL: str = os.getenv('WEBSOCKET_SERVER_URL', f'wss://api.duckycart.me:8000/ws/hardware/{CART_ID}')

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """Load configuration from environment file"""
        if env_file:
            env_path = os.path.join(os.path.dirname(__file__), os.pardir, env_file)
            # print(f"Loading configuration from {env_path}")
            if os.path.exists(env_path):
                load_dotenv(env_path)
                # print("Loaded .env variables:", os.getenv("API_HOST"))  # Debug
            else:
                print(".env file not found! Using defaults.")
        return cls()

# Global config instance
config = Config.load_from_env('.env')
# print(f"Configuration loaded: {config}")
