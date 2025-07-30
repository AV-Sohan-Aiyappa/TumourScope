from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import numpy as np
from datetime import datetime
import base64
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow requests from the React app
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

# Increase max content length to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store results in memory (in a real application, you'd use a database)
results = []

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("Received upload request")
        
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            logger.info(f"Processing file: {file.filename}")
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # Save original file
            original_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(original_path)
            logger.info(f"Saved original file to: {original_path}")
            
            # Process the image (simulate tumor detection)
            img = cv2.imread(original_path)
            if img is None:
                logger.error("Failed to read image")
                return jsonify({'error': 'Failed to process image'}), 400
                
            processed_img = img.copy()
            
            # Simulate tumor detection (random for demo)
            prediction = 'tumor' if np.random.random() > 0.5 else 'normal'
            confidence = np.random.uniform(0.7, 0.99)
            logger.info(f"Prediction: {prediction}, Confidence: {confidence}")
            
            # Add overlay for visualization
            if prediction == 'tumor':
                # Draw a red circle to simulate tumor location
                center = (img.shape[1]//2, img.shape[0]//2)
                radius = min(img.shape[0], img.shape[1])//4
                cv2.circle(processed_img, center, radius, (0, 0, 255), 2)
            
            # Save processed image
            processed_filename = 'processed_' + filename
            processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
            cv2.imwrite(processed_path, processed_img)
            logger.info(f"Saved processed image to: {processed_path}")
            
            # Create result entry
            result = {
                'id': len(results) + 1,
                'date': datetime.now().isoformat(),
                'prediction': prediction,
                'confidence': float(confidence),
                'original_image_url': f'/api/images/original/{filename}',
                'processed_image_url': f'/api/images/processed/{processed_filename}'
            }
            results.append(result)
            
            logger.info("Upload and processing completed successfully")
            return jsonify(result)
        
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    return jsonify(results)

@app.route('/api/images/original/<filename>')
def get_original_image(filename):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    except Exception as e:
        logger.error(f"Error serving original image: {str(e)}")
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/images/processed/<filename>')
def get_processed_image(filename):
    try:
        return send_file(os.path.join(PROCESSED_FOLDER, filename))
    except Exception as e:
        logger.error(f"Error serving processed image: {str(e)}")
        return jsonify({'error': 'Image not found'}), 404

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(debug=True, port=5000) 