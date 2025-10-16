# src/validation/ml_detector.py
import pickle
import numpy as np
import os
import pandas as pd
from sklearn.ensemble import IsolationForest 
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from sklearn.ensemble import IsolationForest 

# --- Function to Load the Saved Model (Remains the same) ---
def load_anomaly_model(model_path: str) -> 'IsolationForest':
    """Loads the trained Isolation Forest model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained ML model not found at: {model_path}")
        
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    
    return model

# --- Function to Run the Anomaly Check (Remains the same) ---
def check_performance_anomaly(model: 'IsolationForest', current_latency_ms: float) -> bool:
    """Predicts if the current latency (ms) is an anomaly."""
    # Input data must be 2D: [[value]]
    input_data = np.array([[current_latency_ms]])
    prediction = model.predict(input_data)
    return prediction[0] == -1

# --- NEW: Function to Calculate the Learned Range ---
def calculate_normal_range(model: 'IsolationForest', historical_df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculates the minimum and maximum latency values the model classifies as 'normal'.
    
    Returns:
        Tuple[float, float]: (min_normal_latency_s, max_normal_latency_s)
    """
    if historical_df.empty:
        return 0, 0
        
    historical_data_ms = historical_df['latency_ms'].values.reshape(-1, 1)
    
    # 1. Predict the status (+1=Normal, -1=Anomaly) on the historical data
    predictions = model.predict(historical_data_ms)
    
    # 2. Filter the historical data to include only 'Normal' points (+1)
    normal_data_ms = historical_data_ms[predictions == 1]
    
    if normal_data_ms.size == 0:
        # This occurs if the model is too strict and flags everything as an anomaly
        return 0, 0
        
    # 3. Calculate the boundaries and convert back to seconds
    min_latency = np.min(normal_data_ms) / 1000  # Convert back to seconds
    max_latency = np.max(normal_data_ms) / 1000  # Convert back to seconds
    
    return min_latency, max_latency