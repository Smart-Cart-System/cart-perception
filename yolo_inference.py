from ultralytics import YOLO
import cv2

# Load the YOLO model
model = YOLO('models/YOLO8n10-best.pt')

def yolo_inference(image):
    """Perform YOLO model inference on the given image."""
    results = model(image, verbose=False) 

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
    
    return cropped_image