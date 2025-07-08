from enum import Enum, auto

class CartState(Enum):
    """Enum representing possible states of the cart system."""
    NORMAL = auto()
    UNSCANNED_ADDED_ITEMS = auto()
    WAITING_FOR_REMOVAL_SCAN = auto()
    PAYMENT_PROCESSING = auto()  # Added for payment processing state
    FRAUD_DETECTED = auto()      # Added for fraud detection
    IDLE = auto()                # Added for idle state
