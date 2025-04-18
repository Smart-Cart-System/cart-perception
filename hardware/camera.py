import cv2
from pyzbar import pyzbar

def set_camera_properties(cap):
    """Configure camera settings for better capture quality."""
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)


def main():
    # Initialize webcam (0 default camera)
    cap = cv2.VideoCapture(1)
    set_camera_properties(cap=cap)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    while True:
        # Read frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Decode barcodes in the frame
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            # Extract bounding box coordinates
            x, y, w, h = barcode.rect
            # Draw a green rectangle around the barcode
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Decode barcode data and type
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            text = f"{barcode_data} ({barcode_type})"

            # Put the decoded text above the barcode in green
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2)

        # Display the resulting frame
        cv2.imshow('Live Barcode Scanner', frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
