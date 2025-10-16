# src/validation/ml_detector.py
import pickle
import numpy as np
import os
from sklearn.ensemble import IsolationForest 
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sklearn.ensemble import IsolationForest 

# --- Function to Load the Saved Model ---
def load_anomaly_model(model_path: str) -> 'IsolationForest':
    """Loads the trained Isolation Forest model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained ML model not found at: {model_path}")
        
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    
    return model

# --- Function to Run the Anomaly Check ---
def check_performance_anomaly(model: 'IsolationForest', current_latency_ms: float) -> bool:
    """
    Uses the loaded ML model to predict if the current latency is an anomaly.
    The model was trained on raw NumPy values, so we must predict with a raw NumPy array.
    """
    
    # Input data must be 2D: [[value]]
    input_data = np.array([[current_latency_ms]])
    
    # predict() returns -1 for anomaly (outlier) and +1 for normal (inlier)
    prediction = model.predict(input_data)
    
    return prediction[0] == -1