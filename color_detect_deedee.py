import cv2
import numpy as np

# Function to do nothing (used as a placeholder for the trackbar callback)
def nothing(x):
    pass

# Initialize the webcam or use a video file
cap = cv2.VideoCapture(0)

# Create a window for the trackbars
cv2.namedWindow('Trackbars')

# Create trackbars to adjust the lower and upper HSV values
cv2.createTrackbar('Lower H', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('Lower S', 'Trackbars', 0, 255, nothing)
cv2.createTrackbar('Lower V', 'Trackbars', 0, 255, nothing)
cv2.createTrackbar('Upper H', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('Upper S', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('Upper V', 'Trackbars', 255, 255, nothing)

# Create trackbars to tune the object size
cv2.createTrackbar('Min Area', 'Trackbars', 0, 1000, nothing)
cv2.createTrackbar('Max Area', 'Trackbars', 1000, 5000, nothing)

# Create trackbars to define the rectangular region of interest (ROI)
cv2.createTrackbar('ROI X', 'Trackbars', 0, 640, nothing)
cv2.createTrackbar('ROI Y', 'Trackbars', 0, 480, nothing)
cv2.createTrackbar('ROI Width', 'Trackbars', 640, 640, nothing)
cv2.createTrackbar('ROI Height', 'Trackbars', 480, 480, nothing)

while True:
    # Read a frame from the camera
    ret, frame = cap.read()

    if not ret:
        break

    # Get the current trackbar positions
    lower_h = cv2.getTrackbarPos('Lower H', 'Trackbars')
    lower_s = cv2.getTrackbarPos('Lower S', 'Trackbars')
    lower_v = cv2.getTrackbarPos('Lower V', 'Trackbars')
    upper_h = cv2.getTrackbarPos('Upper H', 'Trackbars')
    upper_s = cv2.getTrackbarPos('Upper S', 'Trackbars')
    upper_v = cv2.getTrackbarPos('Upper V', 'Trackbars')

    min_area = cv2.getTrackbarPos('Min Area', 'Trackbars')
    max_area = cv2.getTrackbarPos('Max Area', 'Trackbars')

    roi_x = cv2.getTrackbarPos('ROI X', 'Trackbars')
    roi_y = cv2.getTrackbarPos('ROI Y', 'Trackbars')
    roi_width = cv2.getTrackbarPos('ROI Width', 'Trackbars')
    roi_height = cv2.getTrackbarPos('ROI Height', 'Trackbars')

    # Define the lower and upper HSV thresholds
    lower_color = np.array([lower_h, lower_s, lower_v])
    upper_color = np.array([upper_h, upper_s, upper_v])

    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create a mask using the defined HSV thresholds
    mask = cv2.inRange(hsv_frame, lower_color, upper_color)

    # Apply the mask to the original frame
    masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

    # Crop the frame based on the defined ROI
    roi_frame = masked_frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

    # Find contours in the ROI
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on object size
    filtered_contours = [contour for contour in contours if min_area < cv2.contourArea(contour) < max_area]

    # Draw rectangles around detected objects
    for contour in filtered_contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the original frame, masked frame, and ROI frame
    cv2.imshow('Original', frame)
    cv2.imshow('Masked Frame', masked_frame)
    cv2.imshow('ROI Frame', roi_frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close OpenCV windows
cap.release()
cv2.destroyAllWindows()

