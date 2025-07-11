import cv2
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from utils.preprocessing import preprocess_image

# Dictionary to store barcode occurrences
barcode_counts = {}

def read_barcode_pyzbar(image):
    """Decode only EAN-13 barcodes using PyZbar."""
    # Resize for better performance
    resized_img = cv2.resize(image, None, fx=0.7, fy=0.7, interpolation=cv2.INTER_CUBIC)
    
    # Check if image is already grayscale
    if len(resized_img.shape) == 2 or (len(resized_img.shape) == 3 and resized_img.shape[2] == 1):
        gray = resized_img
    else:
        gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
    
    # Try detecting barcodes
    barcodes = decode(gray)
    
    for barcode in barcodes:
        if barcode.type == "EAN13":  # Filter only EAN-13 barcodes
            return barcode.data.decode('utf-8')

    return None

def detect_barcode(image):
    """Detect barcode using improved detection logic and track occurrences."""
    # First try with grayscale processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Read barcode from preprocessed & raw image
    barcode_number = read_barcode_pyzbar(image) or read_barcode_pyzbar(gray) 
    
    if barcode_number:
        # Update occurrence count
        barcode_counts[barcode_number] = barcode_counts.get(barcode_number, 0) + 1

        # Print barcode only if detected 3 times or more
        if barcode_counts[barcode_number] >= 2:
            print(f"Confirmed Barcode: {barcode_number}")
            barcode_counts[barcode_number] = 0

    return int(barcode_number) if barcode_number else None