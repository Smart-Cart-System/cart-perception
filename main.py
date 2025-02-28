import cv2
from camera import set_camera_properties
from barcode_detection import detect_barcode
from api_interaction import send_barcode_to_server

def main():
    """Main function to capture video and detect barcodes in real-time."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    set_camera_properties(cap)
    focus_value = 400

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        barcode_number = detect_barcode(frame)
        if barcode_number:
            send_barcode_to_server(barcode_number, "cart123", 1)
        
        cv2.imshow('Camera Preview', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('t'):
            focus_value += 10
            cap.set(cv2.CAP_PROP_FOCUS, focus_value)
            print("focus:", focus_value)
        elif key == ord('y'):
            focus_value -= 10
            cap.set(cv2.CAP_PROP_FOCUS, focus_value)
            print("focus:", focus_value)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()