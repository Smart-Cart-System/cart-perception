from core.cart_state import CartState
from api.api_interaction import Ambigous
from core.config import Config

class WeightHandlers:
    """Handler methods for weight-related functionality."""
    
    @staticmethod
    def check_item_returned(system, current_weight):
        """Check if an item was put back during removal wait state."""
        tolerance = max(Config.WEIGHT_TOLERANCE, abs(system.removal_weight_diff) * 0.05)  # 5% or min tolerance
        
        if abs(current_weight - system.expected_weight_before_removal) < tolerance:
            print("Weight returned to normal, item was likely put back")
            print("Cancelling removal wait")
            system.api.cancel_warning()
            system.state = CartState.NORMAL
            system.removal_candidates = []

    @staticmethod
    def handle_weight_increase(system, weight_diff):
        """Handle a weight increase event."""
        # Case 1: Weight increase with pending barcode (adding product)
        if weight_diff > 0 and system.cart.pending_weight_change and system.cart.last_scanned_barcode:
            system.api.add_item_to_cart(system.cart.last_scanned_barcode, weight_diff)
            system.cart.add_item(system.cart.last_scanned_barcode, weight_diff)
            system.speaker.item_added()
        # Case 2: Weight increase without pending barcode (unknown addition)
        elif weight_diff > 0:
            WeightHandlers.handle_unscanned_item_addition(system, weight_diff)

    @staticmethod
    def handle_unscanned_item_addition(system, weight_diff):
        """Handle addition of an item without prior barcode scan."""
        if system.state == CartState.WAITING_FOR_SCAN:
            # Add to the unscanned weight
            system.unscanned_weight += weight_diff
        else:
            # Start waiting for scan
            system.api.report_fraud_warning(Ambigous.ADDED)
            system.state = CartState.WAITING_FOR_SCAN
            system.unscanned_weight = weight_diff
        
        # Prompt user to scan barcode
        system.speaker.warning()
        print(f"WARNING: Item added without scanning barcode. Weight: {system.unscanned_weight:.2f}g")
        print("Please scan the barcode of the added item!")

    @staticmethod
    def handle_weight_decrease(system, weight_diff, current_weight):
        """Handle a weight decrease event."""
        # If waiting for scan, check if weight returned to normal
        if system.state == CartState.WAITING_FOR_SCAN:
            expected_weight = system.cart.total_expected_weight
            if abs(current_weight - expected_weight) < WEIGHT_TOLERANCE:
                print("Weight returned to normal, cancelling scan request")
                system.api.cancel_warning()
                system.state = CartState.NORMAL
                system.unscanned_weight = 0
        else:
            # Normal item removal process
            WeightHandlers.process_item_removal(system, weight_diff, current_weight)

    @staticmethod
    def process_item_removal(system, weight_diff, current_weight):
        """Process removal of an item from the cart."""
        matches = system.cart.find_removed_item(weight_diff)
        
        if len(matches) == 1:
            # Clear match for removed item
            barcode, item_data = matches[0]
            print(f"Removed item: {barcode}, weight: {item_data['weight']:.2f}g")
            system.api.remove_item_from_cart(barcode)
            system.cart.remove_item(barcode)
            system.speaker.item_removed()
        else:
            # Ambiguous removal - multiple potential matches
            print(f"Ambiguous removal: {len(matches)} items match the weight {abs(weight_diff):.2f}g")
            print("Please scan the barcode of the removed item")
            print("Possible matches:", [b for b, _ in matches])
            
            # Enter waiting for removal scan state
            system.api.report_fraud_warning(Ambigous.REMOVED)
            system.state = CartState.WAITING_FOR_REMOVAL_SCAN
            system.removal_candidates = matches
            system.removal_weight_diff = weight_diff
            system.expected_weight_before_removal = current_weight - weight_diff
            system.speaker.warning()

    @staticmethod
    def check_weight_normalized(system, current_weight):
        """Check if weight has returned to expected value while waiting for scan."""
        expected_weight = system.cart.total_expected_weight
        if abs(current_weight - expected_weight) < WEIGHT_TOLERANCE:
            print("Weight returned to normal, cancelling scan request")
            system.api.cancel_warning()
            system.state = CartState.NORMAL
            system.unscanned_weight = 0
