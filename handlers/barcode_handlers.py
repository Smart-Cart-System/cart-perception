import time
from core.cart_state import CartState

class BarcodeHandlers:
    """Handler methods for barcode-related functionality."""
    
    @staticmethod
    def handle_during_scan_wait(system, barcode_number):
        """Handle barcode scan when waiting for an item to be scanned after weight addition."""
        print(f"Barcode scanned after weight addition: {barcode_number}")
        system.api.add_item_to_cart(barcode_number, system.unscanned_weight)
        system.cart.add_item(barcode_number, system.unscanned_weight)
        system.state = CartState.NORMAL
        system.unscanned_weight = 0
        system.buzzer.item_added()

    @staticmethod
    def handle_during_removal_wait(system, barcode_number):
        """Handle barcode scan when waiting for confirmation of removed item."""
        found = False
        for candidate_barcode, _ in system.removal_candidates:
            if barcode_number == candidate_barcode:
                print(f"Confirmed removal of item: {barcode_number}")
                system.api.remove_item_from_cart(barcode_number)
                system.cart.remove_item(barcode_number)
                found = True
                break
        
        if found:
            system.speaker.item_removed()
            system.state = CartState.NORMAL
            system.removal_candidates = []
            time.sleep(2)  # Wait for user to see the confirmation
        else:
            system.speaker.warning()
            print(f"Warning: Scanned barcode {barcode_number} does not match any removal candidates")
            print(f"Valid candidates are: {[b for b, _ in system.removal_candidates]}")
            print("Please scan the correct barcode of the removed item")

    @staticmethod
    def handle_normal(system, barcode_number):
        """Handle barcode scan during normal operation."""
        if barcode_number != system.cart.last_scanned_barcode:
            print(f"New barcode detected: {barcode_number}")
            system.api.read_item(barcode_number)
            system.cart.set_pending_barcode(barcode_number)
