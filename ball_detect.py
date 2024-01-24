import cv2
import numpy as np

# Function to filter contours based on size
def filter_contours(contours, min_area, max_area):
    return [contour for contour in contours if min_area < cv2.contourArea(contour) < max_area]

# Function to calculate distance between two points
def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# Initialize the webcam or use a video file
cap = cv2.VideoCapture(0)

# Define the lower and upper HSV thresholds for blue and red colors
lower_blue = np.array([88, 50, 50])
upper_blue = np.array([125, 255, 255])

lower_red = np.array([0, 36, 60])
upper_red = np.array([12, 255, 255])

lower_yellow = np.array([26, 94, 55])
upper_yellow = np.array([46, 208, 150])

# Define the ROI coordinates
roi_x = 0
roi_y = 81
roi_width = 556
roi_height = 309

while True:
    # Read a frame from the camera
    ret, frame = cap.read()

    if not ret:
        break

    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create masks for blue and red colors
    blue_mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
    red_mask = cv2.inRange(hsv_frame, lower_red, upper_red)
    yellow_mask = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)
  
    # Combine blue and red and black masks
    combined_mask = cv2.bitwise_or(blue_mask, red_mask)
    combined_mask = cv2.bitwise_or(yellow_mask, combined_mask)

    # Apply the combined mask to the original frame
    masked_frame = cv2.bitwise_and(frame, frame, mask=combined_mask)

    # Crop the frame based on the defined ROI
    roi_frame = masked_frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

    # Find contours in the ROI
    contours, _ = cv2.findContours(combined_mask[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width].copy(),
                                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on object size
    filtered_contours = filter_contours(contours, 50, 200)

    # Draw rectangles around detected objects in the ROI
    for contour in filtered_contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(roi_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Get the center of the object
        object_center = (x + w // 2, y + h // 2)

        # Calculate and display HSV values
        hsv_values = hsv_frame[y + h // 2, x + w // 2]
        hsv_text = f'HSV: {hsv_values[0]}, {hsv_values[1]}, {hsv_values[2]}'
        cv2.putText(frame, hsv_text, (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Calculate and display object center coordinates
        center_text = f'Center: ({object_center[0]}, {object_center[1]})'
        cv2.putText(frame, center_text, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Calculate and display distance between object centers
        if len(filtered_contours) >= 2:
            for other_contour in filtered_contours:
                if other_contour is not contour:
                    other_x, other_y, _, _ = cv2.boundingRect(other_contour)
                    other_center = (other_x + w // 2, other_y + h // 2)
                    distance = calculate_distance(object_center, other_center)
                    distance_text = f'Distance: {distance:.2f}'
                    cv2.putText(frame, distance_text, (x, y + h + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    if (distance < (1.1*(w+h)/2)):
                        cv2.putText(frame, "COLLISION", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Draw a rectangle around the detected object and mark its size
        cv2.rectangle(frame, (x + roi_x, y + roi_y), (x + roi_x + w, y + roi_y + h), (0, 255, 0), 2)
        size_text = f'Size: {cv2.contourArea(contour):.2f}'
        cv2.putText(frame, size_text, (x + roi_x, y + roi_y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Draw a rectangle around the ROI
    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), (255, 0, 0), 2)

    # Display the original frame
    cv2.imshow('Camera Feed', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close OpenCV windows
cap.release()
cv2.destroyAllWindows()

