import cv2
import numpy as np
import threading
import time

class ThreadedAprilTagCamera:
    """Threaded camera class for AprilTag detection"""
    
    def __init__(self, camera_id=2, tag_family="tag36h11"):
        self.camera_id = camera_id
        self.tag_family = tag_family
        self.running = False
        self.frame = None
        self.latest_tag_id = None
        self.lock = threading.Lock()
        
        # Initialize detector
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        
        # Initialize camera
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_id}")
            
        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cap.set(cv2.CAP_PROP_FOCUS, 400)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        
        # Start thread
        self.thread = threading.Thread(target=self._update, args=(), name="AprilTagCameraThread")
        self.thread.daemon = True

    def start(self):
        """Start the camera thread"""
        self.running = True
        self.thread.start()
        return self

    def _update(self):
        """Update thread that continuously reads frames and detects tags"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect tags
            corners, ids, rejected = self.detector.detectMarkers(gray)
            
            if ids is not None:
                # Find tag closest to center
                frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                min_distance_sq = float('inf')
                closest_tag_id = None
                
                for i, tag_id in enumerate(ids):
                    center = corners[i][0].mean(axis=0).astype(int)
                    distance_sq = ((center[0] - frame_center[0])**2 + 
                                 (center[1] - frame_center[1])**2)
                    
                    if distance_sq < min_distance_sq:
                        min_distance_sq = distance_sq
                        closest_tag_id = tag_id[0]
                
                # Update latest tag with thread safety
                with self.lock:
                    self.latest_tag_id = closest_tag_id
                    self.frame = frame
            else:
                with self.lock:
                    self.latest_tag_id = None
                    self.frame = frame

            time.sleep(0.01)  # Small delay to prevent excessive CPU usage

    def get_latest_tag(self):
        """Get the latest detected tag ID with thread safety"""
        with self.lock:
            return self.latest_tag_id

    def get_frame(self):
        """Get the latest frame with thread safety"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def release(self):
        """Stop the thread and release the camera"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()

    @property
    def is_running(self):
        """Property that returns the running state of the camera thread."""
        return self.running

    def stop(self):
        """Stop the camera thread"""
        self.running = False
        if self.thread.is_alive():
                self.thread.join()

if __name__ == "__main__":
    camera = ThreadedAprilTagCamera()
    camera.start()
    
    try:
        while True:
            tag_id = camera.get_latest_tag()
            frame = camera.get_frame()
            
            if frame is not None:
                # cv2.imshow("AprilTag Camera", frame)
                if tag_id is not None:
                    print(f"Detected Tag ID: {tag_id}")
                else:
                    print("No tags detected")
                
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released and window closed.")