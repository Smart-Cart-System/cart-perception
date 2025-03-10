import cv2
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from preprocessing import preprocess_image
from yolo_inference import yolo_inference
# Load the YOLO model
# model = YOLO('models/YOLO8n10-best.pt')

# Dictionary to store barcode occurrences
barcode_counts = {}

def read_barcode_pyzbar(cropped_image):
    """Decode only EAN-13 barcodes using PyZbar."""
    barcodes = decode(cropped_image)
    for barcode in barcodes:
        if barcode.type == "EAN13":  # Filter only EAN-13 barcodes
            return barcode.data.decode('utf-8')

    return None

def detect_barcode(image):
    """Detect barcode using YOLO, enlarge bounding box width, and track occurrences."""
    # cropped_image = yolo_inference(image)
    # processed_image = preprocess_image(cropped_image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Read barcode from preprocessed & raw cropped image
    barcode_number = read_barcode_pyzbar(image) or read_barcode_pyzbar(gray) 
    # print(f"Detected Barcode: {barcode_number}")
    if barcode_number:
        # Update occurrence count
        barcode_counts[barcode_number] = barcode_counts.get(barcode_number, 0) + 1

        # Print barcode only if detected 3 times or more
        if barcode_counts[barcode_number] >= 3:
            print(f"Confirmed Barcode: {barcode_number}")
            barcode_counts[barcode_number] = 0

    return int(barcode_number) if barcode_number else None