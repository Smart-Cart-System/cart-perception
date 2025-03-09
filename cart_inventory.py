class CartInventory:
    """Class for managing cart inventory with weight tracking."""
    
    def __init__(self, weight_match_threshold=0.10):
        """Initialize cart inventory tracking."""
        self.items = {}  # {barcode: {"weight": weight_per_unit, "quantity": count}}
        self.last_scanned_barcode = None
        self.pending_weight_change = False
        self.weight_match_threshold = weight_match_threshold  # 10% threshold for weight matching
        self.total_expected_weight = 0  # Track the total expected weight of items
        
    def add_item(self, barcode, weight):
        """Add an item to the cart inventory."""
        if barcode in self.items:
            # Item already exists, increase quantity
            self.items[barcode]["quantity"] += 1
            print(f"Increased quantity of {barcode} to {self.items[barcode]['quantity']}")
        else:
            # New item
            self.items[barcode] = {"weight": weight, "quantity": 1}
            print(f"Added new item {barcode} with weight {weight:.2f}g")
        
        # Update total expected weight
        self.total_expected_weight += weight
        print(f"Cart total weight: {self.total_expected_weight:.2f}g")
        
        self.last_scanned_barcode = None
        self.pending_weight_change = False
    
    def find_removed_item(self, weight_diff):
        """Find item matching the weight difference within threshold."""
        abs_diff = abs(weight_diff)
        matches = []
        
        for barcode, item_data in self.items.items():
            item_weight = item_data["weight"]
            # Check if weight difference matches item weight within threshold
            if abs(abs_diff - item_weight) <= item_weight * self.weight_match_threshold:
                matches.append((barcode, item_data))
        
        return matches
    
    def remove_item(self, barcode):
        """Remove an item from the cart or decrease its quantity."""
        if barcode not in self.items:
            return False
        
        # Update total expected weight
        self.total_expected_weight -= self.items[barcode]["weight"]
            
        if self.items[barcode]["quantity"] > 1:
            self.items[barcode]["quantity"] -= 1
            print(f"Decreased quantity of {barcode} to {self.items[barcode]['quantity']}")
        else:
            del self.items[barcode]
            print(f"Removed item {barcode} from cart")
        
        print(f"Cart total weight: {self.total_expected_weight:.2f}g")
        return True
    
    def set_pending_barcode(self, barcode):
        """Set the last scanned barcode as pending for weight change."""
        self.last_scanned_barcode = barcode
        self.pending_weight_change = True
    
    def get_cart_summary(self):
        """Get a summary of items in the cart."""
        if not self.items:
            return "Cart is empty"
            
        summary = "----- Current Cart Contents -----\n"
        total_items = 0
        for barcode, item_data in self.items.items():
            summary += f"Item: {barcode}, Weight: {item_data['weight']:.2f}g, Quantity: {item_data['quantity']}\n"
            total_items += item_data["quantity"]
        summary += f"Total unique items: {len(self.items)}, Total quantity: {total_items}\n"
        summary += f"Total expected weight: {self.total_expected_weight:.2f}g\n"
        summary += "------------------------------"
        return summary
    
    def clear_cart(self):
        """Clear all items from the cart."""
        self.items.clear()
        self.last_scanned_barcode = None
        self.pending_weight_change = False
        self.total_expected_weight = 0
        print("Cart cleared")