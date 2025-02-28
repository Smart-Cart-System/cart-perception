import cv2
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from preprocessing import preprocess_image

# Load the YOLO model
model = YOLO('YOLO8n10-best.pt')

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
    results = model(image, verbose=False)  # Silent YOLO inference

    if len(results) == 0 or len(results[0].boxes) == 0:
        return None  

    bbox = results[0].boxes.xyxy[0].tolist()  # Convert to list
    x1, y1, x2, y2 = map(int, bbox)

    # Enlarge the bounding box width
    expansion = 20
    x1 = max(0, x1 - expansion)
    x2 = min(image.shape[1], x2 + expansion)

    # Draw bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Extract ROI and preprocess
    cropped_image = image[y1:y2, x1:x2]
    processed_image = preprocess_image(cropped_image)

    # Read barcode from preprocessed & raw cropped image
    barcode_number = read_barcode_pyzbar(processed_image) or read_barcode_pyzbar(cropped_image)

    if barcode_number:
        # Update occurrence count
        barcode_counts[barcode_number] = barcode_counts.get(barcode_number, 0) + 1

        # Print barcode only if detected 3 times or more
        if barcode_counts[barcode_number] >= 3:
            print(f"Confirmed Barcode: {barcode_number}")
            barcode_counts[barcode_number] = 0

        # Display detected barcode on frame
        cv2.putText(image, barcode_number, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2, cv2.LINE_AA)

    return barcode_number