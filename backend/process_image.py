import cv2
import numpy as np
import sys
import os

def overlay_smiley(input_path, output_path):
    try:
        # Read the input image
        img = cv2.imread(input_path)
        if img is None:
            raise Exception("Failed to read input image")

        # Get image dimensions
        height, width = img.shape[:2]

        # Create a smiley face
        center = (width // 2, height // 2)
        radius = min(width, height) // 4
        color = (0, 255, 0)  # Green color
        thickness = 2

        # Draw face circle
        cv2.circle(img, center, radius, color, thickness)

        # Draw eyes
        eye_radius = radius // 4
        left_eye = (center[0] - radius//2, center[1] - radius//2)
        right_eye = (center[0] + radius//2, center[1] - radius//2)
        cv2.circle(img, left_eye, eye_radius, color, thickness)
        cv2.circle(img, right_eye, eye_radius, color, thickness)

        # Draw smile
        smile_radius = radius // 2
        smile_center = (center[0], center[1] + radius//4)
        start_angle = 0
        end_angle = 180
        cv2.ellipse(img, smile_center, (smile_radius, smile_radius//2), 0, start_angle, end_angle, color, thickness)

        # Save the processed image
        cv2.imwrite(output_path, img)
        return True

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_image.py <input_path> <output_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist")
        sys.exit(1)

    success = overlay_smiley(input_path, output_path)
    sys.exit(0 if success else 1) 