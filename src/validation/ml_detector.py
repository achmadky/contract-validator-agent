# src/validation/ml_detector.py
import pickle
import numpy as np
import os
from sklearn.ensemble import IsolationForest # Only for type hinting

# --- ML Utility Functions ---

def load_anomaly_model(model_path: str) -> IsolationForest:
    """Loads the trained ML model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained ML model not found at: {model_path}")
        
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    return model

def check_performance_anomaly(model: IsolationForest, current_latency: float) -> bool:
    """Predicts if the current latency (ms) is an anomaly."""
    # Model expects data in a 2D array: [[value]]
    input_data = np.array([[current_latency]])
    
    # predict() returns -1 for anomaly (outlier) and +1 for normal (inlier)
    prediction = model.predict(input_data)
    
    return prediction[0] == -1