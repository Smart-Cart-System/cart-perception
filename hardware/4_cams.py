import cv2

# Initialize video captures for 4 cameras
camera_1 = cv2.VideoCapture(0)
camera_2 = cv2.VideoCapture(2)
camera_3 = cv2.VideoCapture(5)
camera_4 = cv2.VideoCapture(6)

# Set the resolution for all cameras
resolution_width = 1280
resolution_height = 720
camera_1.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
camera_1.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
camera_2.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
camera_2.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
camera_3.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
camera_3.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
camera_4.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
camera_4.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)

# Set the FOURCC codec for all cameras
camera_1.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
camera_2.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
camera_3.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
camera_4.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

if not (camera_1.isOpened() or camera_2.isOpened() or camera_3.isOpened() or camera_4.isOpened()):
    print("Error: None of the cameras could be opened.")
    camera_1.release()
    camera_2.release()
    camera_3.release()
    camera_4.release()
    exit()

while True:
    # Read frames from each camera
    ret1, frame1 = camera_1.read() if camera_1.isOpened() else (False, None)
    ret2, frame2 = camera_2.read() if camera_2.isOpened() else (False, None)
    ret3, frame3 = camera_3.read() if camera_3.isOpened() else (False, None)
    ret4, frame4 = camera_4.read() if camera_4.isOpened() else (False, None)

    # Display frames only for cameras that are working
    if ret1:
        cv2.imshow("Camera 1", frame1)
    if ret2:
        cv2.imshow("Camera 2", frame2)
    if ret3:
        cv2.imshow("Camera 3", frame3)
    if ret4:
        cv2.imshow("Camera 4", frame4)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release all cameras and close windows
camera_1.release()
camera_2.release()
camera_3.release()
camera_4.release()
cv2.destroyAllWindows()