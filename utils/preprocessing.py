import cv2
import numpy as np

def preprocess_image(image):
    """Apply sharpening filter to enhance barcode edges."""
    # Check if image is already grayscale (1 channel)
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        gray = image
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sharpening_kernel = np.array([[0, -1, 0], 
                                  [-1, 5, -1], 
                                  [0, -1, 0]])
    
    return cv2.filter2D(gray, -1, sharpening_kernel)