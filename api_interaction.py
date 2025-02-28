import requests
import json
import os

def send_barcode_to_server(barcode, cart_id, user_id):
    """Send barcode data to the server and process the response."""
    # Replace with your API URL
    api_url = os.getenv("API_URL", "http://127.0.0.1:8000/products/scan-barcode")

    # Prepare the barcode data
    barcode_data = {
        "barcode": barcode,
        "cart_id": cart_id,
        "user_id": user_id
    }

    try:
        response = requests.post(api_url, json=barcode_data)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return
    # Process response
    if response.status_code == 200:
        product_data = response.json()
        print(f"Added {product_data['description']} to cart")
    else:
        print(f"Error {response.status_code}: {response.text}")
