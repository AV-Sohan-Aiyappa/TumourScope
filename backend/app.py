from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import cv2
import numpy as np
from tumor_detector import TraditionalTumorDetector
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize the tumor detector with the actual dataset paths
dataset_paths = {
    'normal': r"C:\Users\sohan\OneDrive\Desktop\TumorScope\Datasets\normal",
    'benign': r"C:\Users\sohan\OneDrive\Desktop\TumorScope\Datasets\benign",
    'malignant': r"C:\Users\sohan\OneDrive\Desktop\TumorScope\Datasets\malignant"
}

# Create a custom dataset loader that uses the specific paths
class CustomTumorDetector(TraditionalTumorDetector):
    def load_dataset(self):
        X = []
        y = []

        for label, (category, path) in enumerate(dataset_paths.items()):
            if not os.path.exists(path):
                logger.error(f"Dataset path not found: {path}")
                continue

            logger.info(f"Processing {category} images from {path}...")
            image_count = 0

            for img_name in os.listdir(path):
                if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue

                img_path = os.path.join(path, img_name)
                try:
                    img = cv2.imread(img_path)
                    if img is None:
                        logger.warning(f"Skipping unreadable image: {img_path}")
                        continue

                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    features = self.extract_features(img)
                    X.append(features)
                    y.append(label)
                    image_count += 1

                    if image_count % 10 == 0:
                        logger.info(f"  Processed {image_count} {category} images")

                except Exception as e:
                    logger.error(f"Error processing {img_path}: {e}")

            logger.info(f"Completed {category}: {image_count} images")

        return np.array(X), np.array(y)

# Initialize the detector
detector = CustomTumorDetector(dataset_path='dummy')  # Path is not used in custom loader

# Train the model on startup
try:
    logger.info("Training the model with your dataset...")
    detector.train_model(model_type='random_forest')
    logger.info("Model training completed successfully!")
except Exception as e:
    logger.error(f"Error during model training: {str(e)}")
    logger.error("Please check if the dataset paths are correct and contain valid images.")

# Import the Result model for database storage
import sys
import os
import requests

# Add the parent directory to sys.path to import Node.js models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We'll use a temporary in-memory store during processing
# but actual storage will be handled by the Node.js backend
results_history = []

# Node.js backend URL for saving results
NODE_BACKEND_URL = 'http://localhost:3002/api/results/save'
# API key for secure communication between backends
API_KEY = os.environ.get('PYTHON_API_KEY', 'default_dev_key_change_in_production')

@app.route('/api/detect', methods=['POST'])
def detect_tumor():
    try:
        if detector.classifier is None:
            logger.error("Model not trained")
            return jsonify({
                'success': False,
                'error': 'Model not trained. Please check the dataset paths and restart the server.'
            }), 500

        # Get the image from the request
        data = request.json
        logger.info("Received image data")
        
        # Get user_id from request if available
        user_id = data.get('user_id')
        if not user_id:
            logger.warning("No user_id provided in request")
        
        if 'image' not in data:
            logger.error("No image data in request")
            return jsonify({
                'success': False,
                'error': 'No image data received'
            }), 400
            
        try:
            image_data = data['image'].split(',')[1]  # Remove the data URL prefix
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"Error decoding image data: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid image data format'
            }), 400
        
        # Save the image temporarily
        temp_path = 'temp_image.jpg'
        try:
            with open(temp_path, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"Saved temporary image to {temp_path}")
        except Exception as e:
            logger.error(f"Error saving temporary image: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Error saving image'
            }), 500
        
        # Process the image
        try:
            result = detector.highlight_tumor_region(temp_path)
            logger.info("Image processed successfully")
        except Exception as e:
            logger.error(f"Error in highlight_tumor_region: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'Error processing image: {str(e)}'
            }), 500
        
        # Convert images to base64
        def image_to_base64(img):
            try:
                if img is None:
                    return None
                # Ensure the image is in the correct format
                if len(img.shape) == 2:  # If grayscale
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                success, buffer = cv2.imencode('.jpg', img)
                if not success:
                    logger.error("Failed to encode image")
                    return None
                return base64.b64encode(buffer).decode('utf-8')
            except Exception as e:
                logger.error(f"Error converting image to base64: {str(e)}")
                return None
        
        # Clean up
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Error removing temporary file: {str(e)}")
        
        import time
        response_data = {
            'success': True,
            'prediction': result['prediction'],
            'confidence': float(result['confidence']),
            'original': image_to_base64(result['original']),
            'binary': image_to_base64(result['binary']),
            'contours': image_to_base64(result['contours']),
            'overlay': image_to_base64(result['overlay']),
            'is_normal': result.get('is_normal', False),
            'timestamp': int(time.time())
        }
        # Store result in history (including images as base64)
        result_data = {
            'prediction': response_data['prediction'],
            'confidence': response_data['confidence'],
            'timestamp': response_data['timestamp'],
            'original': response_data['original'],
            'binary': response_data['binary'],
            'contours': response_data['contours'],
            'overlay': response_data['overlay'],
            'is_normal': response_data['is_normal']
        }
        
        # Add user_id if available
        if user_id:
            result_data['user_id'] = user_id
            
            # Save result to Node.js database
            try:
                logger.info(f"Saving result to Node.js database for user {user_id}")
                node_response = requests.post(
                    NODE_BACKEND_URL,
                    json=result_data,
                    headers={
                        'Content-Type': 'application/json',
                        'X-API-Key': API_KEY
                    },
                    timeout=5  # 5 second timeout
                )
                
                if node_response.status_code == 201:
                    logger.info(f"Result saved successfully to database with ID: {node_response.json().get('result_id')}")
                else:
                    logger.error(f"Failed to save result to database: {node_response.text}")
            except Exception as e:
                logger.error(f"Error saving result to Node.js database: {str(e)}")
                # Continue processing even if database save fails
            
        results_history.append(result_data)
        # Check if any required image conversion failed
        if response_data['original'] is None:
            logger.error("Error converting original image to base64")
            return jsonify({
                'success': False,
                'error': 'Error processing image'
            }), 500
            
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    # Get user_id from query parameters if available
    user_id = request.args.get('user_id')
    
    if user_id:
        # Filter results by user_id
        filtered_results = [r for r in results_history if r.get('user_id') == int(user_id)]
        return jsonify(filtered_results)
    else:
        # If no user_id provided, return all results (for backward compatibility)
        # In production, this should be restricted to authenticated admin users
        return jsonify(results_history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)