import cv2
from pyzbar.pyzbar import decode
import time

def configure_camera(cap, device_name):
    """Sets the configuration for a given camera."""
    print(f"Configuring {device_name}...")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Start with autofocus ON
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    cap.set(cv2.CAP_PROP_CONTRAST, 80)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, -90)
    print(f"Brightness for {device_name}: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
    print(f"Contrast for {device_name}: {cap.get(cv2.CAP_PROP_CONTRAST)}")

def process_frame(frame, cap, last_af_trigger_time, camera_name):
    """Processes a single frame for barcode detection and handles autofocus."""
    if frame is None:
        return None, last_af_trigger_time

    # Frame downsize
    frame = cv2.resize(frame, None, fx=0.7, fy=0.7, interpolation=cv2.INTER_CUBIC)
    # Grayscale for barcode reader
    thresh = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Barcode detection
    barcodes = decode(thresh)

    # Compute focus measure (sharpness)
    focus_measure = cv2.Laplacian(thresh, cv2.CV_64F).var() + 200

    current_time = time.time()

    # Debug: Show focus measure
    cv2.putText(frame, f"Focus: {focus_measure:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # --- autofocus logic ---
    if (current_time - last_af_trigger_time) > AF_RETRY_DELAY:
        if (focus_measure < FOCUS_THRESHOLD) and not barcodes:
            print(f"Focus blurry on {camera_name} (focus={focus_measure:.2f}), retrying autofocus...")
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            time.sleep(0.05)
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            last_af_trigger_time = current_time

    # Print green rectangle and barcode info
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        text = f"{barcode_type}: {barcode_data}"
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        print(f"[{camera_name}] {barcode_type}: {barcode_data}")

    return frame, last_af_trigger_time

# Camera initialization
cap_left = cv2.VideoCapture("/dev/cam_scan_left")
cap_right = cv2.VideoCapture("/dev/cam_scan_right")

# Camera configuration
configure_camera(cap_left, "Left Camera")
configure_camera(cap_right, "Right Camera")

# Focus threshold and timing
FOCUS_THRESHOLD = 400  # Lower = allows more blur
AF_RETRY_DELAY = 0.8  # seconds before retrying autofocus
last_af_trigger_time_left = 0
last_af_trigger_time_right = 0

while True:
    ret_left, frame_left = cap_left.read()
    ret_right, frame_right = cap_right.read()

    if not ret_left or not ret_right:
        print("Error: Could not read frame from one or both cameras.")
        break

    processed_frame_left, last_af_trigger_time_left = process_frame(
        frame_left, cap_left, last_af_trigger_time_left, "Left"
    )
    processed_frame_right, last_af_trigger_time_right = process_frame(
        frame_right, cap_right, last_af_trigger_time_right, "Right"
    )

    # Combine frames for display
    if processed_frame_left is not None and processed_frame_right is not None:
        combined_frame = cv2.hconcat([processed_frame_left, processed_frame_right])
        cv2.imshow('Barcode Scanner', combined_frame)

    if cv2.waitKey(1) == 27:  # ESC key to exit
        break

cap_left.release()
cap_right.release()
cv2.destroyAllWindows()