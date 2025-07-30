import cv2
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from skimage.feature import graycomatrix, graycoprops
from skimage.feature import local_binary_pattern
from skimage.measure import label, regionprops
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class TraditionalTumorDetector:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path
        self.classes = ['normal', 'benign', 'malignant']
        self.classifier = None

    def extract_features(self, image):
        """Extract relevant features from ultrasound image for tumor detection"""
        try:
            features = []

            # Convert to grayscale if needed
            if len(image.shape) > 2:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            # Resize image
            gray = cv2.resize(gray, (224, 224))

            # Basic intensity features
            features.append(np.mean(gray))  # Mean intensity
            features.append(np.std(gray))   # Standard deviation
            features.append(np.min(gray))   # Min intensity
            features.append(np.max(gray))   # Max intensity

            # Histogram features
            hist = cv2.calcHist([gray], [0], None, [10], [0, 256])
            hist = hist.flatten() / np.sum(hist)  # Normalize
            features.extend(hist)

            # GLCM features
            glcm = graycomatrix(gray, [1], [0, np.pi/4, np.pi/2, 3*np.pi/4],
                               256, symmetric=True, normed=True)

            contrast = graycoprops(glcm, 'contrast').flatten()
            dissimilarity = graycoprops(glcm, 'dissimilarity').flatten()
            homogeneity = graycoprops(glcm, 'homogeneity').flatten()
            energy = graycoprops(glcm, 'energy').flatten()
            correlation = graycoprops(glcm, 'correlation').flatten()

            features.extend(contrast)
            features.extend(dissimilarity)
            features.extend(homogeneity)
            features.extend(energy)
            features.extend(correlation)

            # LBP features
            radius = 3
            n_points = 8 * radius
            lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
            lbp_hist, _ = np.histogram(lbp, bins=n_points+2, range=(0, n_points+2), density=True)
            features.extend(lbp_hist)

            # Shape features
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = np.ones((5,5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            labeled = label(binary)
            regions = regionprops(labeled)

            if regions:
                regions.sort(key=lambda x: x.area, reverse=True)
                largest = regions[0]
                features.append(largest.area)
                features.append(largest.perimeter)
                features.append(largest.eccentricity)
                features.append(largest.equivalent_diameter)
                features.append(largest.solidity)
            else:
                features.extend([0, 0, 0, 0, 0])

            return np.array(features)
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            raise

    def load_dataset(self):
        X = []
        y = []

        for label, category in enumerate(self.classes):
            path = os.path.join(self.dataset_path, category)
            if not os.path.exists(path):
                logger.error(f"Skipping non-existent category: {category}")
                continue

            logger.info(f"Processing {category} images...")
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

    def train_model(self, model_type='random_forest'):
        try:
            logger.info("Extracting features...")
            X, y = self.load_dataset()

            if len(X) == 0:
                raise ValueError("No images could be processed. Check your dataset path.")

            unique, counts = np.unique(y, return_counts=True)
            logger.info("\nClass distribution:")
            for u, c in zip(unique, counts):
                logger.info(f"{self.classes[u]}: {c} images")

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

            logger.info(f"\nTraining on {X_train.shape[0]} samples, testing on {X_test.shape[0]} samples")
            logger.info(f"Feature vector size: {X_train.shape[1]}")

            if model_type == 'random_forest':
                self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_type == 'svm':
                self.classifier = SVC(probability=True, random_state=42)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            logger.info(f"Training {model_type} classifier...")
            self.classifier.fit(X_train, y_train)

            # Evaluate
            y_pred = self.classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"Test accuracy: {accuracy:.4f}")
            logger.info("\nClassification Report:")
            logger.info(classification_report(y_test, y_pred, target_names=self.classes))

            if model_type == 'random_forest':
                importances = self.classifier.feature_importances_
                indices = np.argsort(importances)[::-1]

                logger.info("\nTop 10 most important features:")
                for i in range(min(10, len(importances))):
                    logger.info(f"Feature #{indices[i]}: {importances[indices[i]]:.4f}")

            return self.classifier
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def highlight_tumor_region(self, image_path):
        """Highlight potential tumor regions in an ultrasound image"""
        try:
            if self.classifier is None:
                raise ValueError("Model not trained yet. Call train_model() first.")

            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            features = self.extract_features(img_rgb)
            pred_class = self.classifier.predict([features])[0]
            pred_proba = self.classifier.predict_proba([features])[0]
            confidence = pred_proba[pred_class]

            logger.info(f"Predicted class: {self.classes[pred_class]} (confidence: {confidence:.2f})")

            # If the image is classified as normal, return only the prediction without analysis
            if pred_class == 0:  # 0 is the index for 'normal'
                return {
                    'original': img_rgb,
                    'binary': None,
                    'contours': None,
                    'overlay': None,
                    'prediction': self.classes[pred_class],
                    'confidence': confidence,
                    'is_normal': True
                }

            # Only perform tumor detection analysis for non-normal images
            _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = np.ones((5,5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_area = 100
            valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

            result_img = img_rgb.copy()
            highlight_color = (255, 0, 0)

            cv2.drawContours(result_img, valid_contours, -1, highlight_color, 2)
            mask = np.zeros_like(img_rgb)
            cv2.drawContours(mask, valid_contours, -1, highlight_color, -1)
            overlay = cv2.addWeighted(img_rgb, 0.7, mask, 0.3, 0)

            return {
                'original': img_rgb,
                'binary': binary,
                'contours': result_img,
                'overlay': overlay,
                'prediction': self.classes[pred_class],
                'confidence': confidence,
                'is_normal': False
            }
        except Exception as e:
            logger.error(f"Error highlighting tumor region: {str(e)}")
            raise 