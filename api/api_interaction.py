import requests
import json
from enum import Enum
import os
import sys

# Add the parent directory to the Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config

API_URL = Config.API_HOST
API_KEY = Config.API_KEY

class Ambigous(Enum):
    """Enum for ambigous added and removed items."""
    ADDED = "weight increased"
    REMOVED = "weight decreased"
    
    def __str__(self):
        return self.value

class CartAPI:
    def __init__(self, api_url=API_URL, cart_id=None):
        self.api_url = api_url
        self.headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        self.session_id = self.get_session_by_cart(cart_id) if cart_id else None

    def get_session_by_cart(self, cart_id):
        """Test getting an active session by cart ID"""
        try:
            # Make API request
            url = f"{self.api_url}/customer-session/cart/{cart_id}"
            print(f"Sending GET request to {url}")
            
            response = requests.get(url, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                session_data = response.json()
                print(f"Success! Active session found:")
                print(f"  Session ID: {session_data['session_id']}")
                print(f"  User ID: {session_data['user_id']}")
                print(f"  Cart ID: {session_data['cart_id']}")
                print(f"  Created at: {session_data['created_at']}")
                return session_data['session_id']
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
        
    def read_item(self, barcode):
        """Test reading an item with the barcode scanner"""
        try:
            # Prepare request data
            item_data = {
                "sessionID": int(self.session_id),
                "barcode": int(barcode)
            }
            
            # Make API request
            url = f"{self.api_url}/items/read"
            print(f"Sending POST request to {url}")
            print(f"Request data: {json.dumps(item_data, indent=2)}")
            
            response = requests.post(url, json=item_data, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                product_data = response.json()
                print(f"Success! Item read:")
                print(f"  Item No: {product_data['item_no_']}")
                print(f"  Description: {product_data['description']}")
                print(f"  Arabic Description: {product_data['description_ar']}")
                print(f"  Size: {product_data['product_size']}")
                print(f"  Price: {product_data['unit_price']}")
                return product_data
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
        
    def add_item_to_cart(self, barcode, weight=None):
        """Test adding an item to cart"""
        try:
            # Prepare request data
            item_data = {
                "sessionID": int(self.session_id),
                "barcode": int(barcode)
            }
            
            # Add weight if provided
            if weight is not None:
                item_data["weight"] = float(weight)
            
            # Make API request
            url = f"{self.api_url}/cart-items/add"
            print(f"Sending POST request to {url}")
            print(f"Request data: {json.dumps(item_data, indent=2)}")
            
            response = requests.post(url, json=item_data, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                item_data = response.json()
                print(f"Success! Item added to cart:")
                print(f"  Session ID: {item_data['session_id']}")
                print(f"  Item ID: {item_data['item_id']}")
                print(f"  Quantity: {item_data['quantity']}")
                
                if 'product' in item_data and item_data['product']:
                    print(f"  Product: {item_data['product']['description']}")
                    print(f"  Price: {item_data['product']['unit_price']}")
                
                if item_data.get('saved_weight'):
                    print(f"  Weight: {item_data['saved_weight']}")
                    
                return item_data
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def remove_item_from_cart(self, barcode):
        """Test removing an item from the cart"""
        try:
            # Prepare request data
            item_data = {
                "sessionID": int(self.session_id),
                "barcode": int(barcode)
            }
            
            # Make API request
            url = f"{self.api_url}/cart-items/remove"
            print(f"Sending DELETE request to {url}")
            print(f"Request data: {json.dumps(item_data, indent=2)}")
            
            response = requests.delete(url, json=item_data, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                print(f"Success! {result['message']}")
                
                if result.get('item'):
                    print(f"  Session ID: {result['item']['session_id']}")
                    print(f"  Item ID: {result['item']['item_id']}")
                    print(f"  New Quantity: {result['item']['quantity']}")
                    
                    if result['item'].get('product'):
                        print(f"  Product: {result['item']['product']['description']}")
                
                return result
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def report_fraud_warning(self, warning_type):
        """Report a fraud warning"""
        try:
            # Prepare request data
            warning_data = {
                "session_id": int(self.session_id),
                "type_of_warning": str(warning_type)
            }
            
            # Make API request
            url = f"{self.api_url}/fraud-warnings/"
            print(f"Reporting fraud warning to {url}")
            print(f"Warning type: {warning_type}")
            
            response = requests.post(url, json=warning_data, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                warning_data = response.json()
                print(f"Success! Warning reported (ID: {warning_data['id']})")
                return warning_data
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def cancel_warning(self, barcode=0):
        """Test sending a cart-update notification via WebSocket"""
        try:
            # Prepare request data
            notification_data = {
                "session_id": int(self.session_id),
                "barcode": int(barcode)
            }
            
            # Make API request
            url = f"{self.api_url}/fraud-warnings/notify-cart-update"
            print(f"Sending POST request to {url}")
            print(f"Request data: {json.dumps(notification_data, indent=2)}")
            
            response = requests.post(url, json=notification_data, headers=self.headers)
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                print(f"Success! {result['message']}")
                print(f"WebSocket notification sent to session ID: {self.session_id}")
                print(f"Message type: cart-updated")
                print(f"Barcode: {barcode}")
                return result
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

if __name__ == "__main__":
    api = CartAPI()
    api.get_session_by_cart(1)