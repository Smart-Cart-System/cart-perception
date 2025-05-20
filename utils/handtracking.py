import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Hand Detector
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Define cart area (change these values as per your setup)
CART_X1, CART_Y1 = 100, 300  # Top-left corner
CART_X2, CART_Y2 = 400, 600  # Bottom-right corner

cap = cv2.VideoCapture('/dev/video0')

# Store the previous wrist position for movement tracking
previous_wrist_x, previous_wrist_y = None, None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Flip for natural hand movement
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    # Draw the cart area on the frame
    cv2.rectangle(frame, (CART_X1, CART_Y1), (CART_X2, CART_Y2), (0, 255, 0), 2)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get key points
            index_tip = hand_landmarks.landmark[8]  # Index Finger Tip
            thumb_tip = hand_landmarks.landmark[4]  # Thumb Tip
            wrist = hand_landmarks.landmark[0]  # Wrist

            # Convert to pixel coordinates
            h, w, _ = frame.shape
            index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
            thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
            wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)

            # Draw hand landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect if hand is gripping (thumb and index finger close together)
            grip_distance = np.linalg.norm(np.array([index_x, index_y]) - np.array([thumb_x, thumb_y]))
            is_gripping = grip_distance < 50  # Adjust threshold

            # Check if hand is inside the cart area
            is_inside_cart = CART_X1 < wrist_x < CART_X2 and CART_Y1 < wrist_y < CART_Y2

            # Track movement direction
            movement_text = ""
            if previous_wrist_x is not None and previous_wrist_y is not None:
                movement_vector = np.array([wrist_x - previous_wrist_x, wrist_y - previous_wrist_y])
                movement_magnitude = np.linalg.norm(movement_vector)

                if movement_magnitude > 5:  # Ensure movement is significant
                    if wrist_x > previous_wrist_x:  # Moving Right
                        movement_text = "Moving Right"
                    elif wrist_x < previous_wrist_x:  # Moving Left
                        movement_text = "Moving Left"
                    
                    if wrist_y > previous_wrist_y:  # Moving Down (Into Cart)
                        movement_text = "Moving to Cart"
                    elif wrist_y < previous_wrist_y:  # Moving Up (Out of Cart)
                        movement_text = "Moving Out of Cart"

            # Update previous wrist position
            previous_wrist_x, previous_wrist_y = wrist_x, wrist_y

            # Display status
            if is_gripping:
                cv2.putText(frame, "Holding Item", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            if is_inside_cart:
                cv2.putText(frame, "Hand in Cart", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # Detect if item is placed inside the cart
            if is_gripping and is_inside_cart:
                cv2.putText(frame, "Item Placed in Cart!", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Display movement direction
            if movement_text:
                cv2.putText(frame, movement_text, (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    # Show the frame
    cv2.imshow("Hand Tracking - Cart Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()