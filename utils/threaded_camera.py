import cv2
import threading
import time

class ThreadedCamera:
    """A class to read frames from a camera in a separate thread."""

    def __init__(self, src=0, name="ThreadedCamera"):
        """Initialize the threaded camera."""
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            print(f"Error: Could not open video source: {src}")
            self.running = False
            self.frame = None
            self.grabbed = False
            return

        self.grabbed, self.frame = self.stream.read()
        self.name = name
        self.running = False
        self.thread = None
        self.start()

    def isOpened(self):
        """Check if the camera is opened."""
        return self.stream.isOpened()

    def start(self):
        """Start the thread to read frames from the video stream."""
        if self.running:
            print(f"[{self.name}] is already running.")
            return self

        self.running = True
        self.thread = threading.Thread(target=self.update, name=self.name, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def update(self):
        """The target function for the reading thread."""
        while self.running:
            self.grabbed, self.frame = self.stream.read()

    def read(self):
        """Return the latest frame."""
        return self.frame

    @property
    def cap(self):
        return self.stream
        
    @property
    def is_running(self):
        """Property that returns the running state of the camera thread."""
        return self.running
    def stop(self):
        """Stop the thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def release(self):
        """Release the camera resource."""
        self.stop()
        self.stream.release()
