# utils/train_anomaly_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
import time

# --- CONFIGURATION ---
MODEL_DIR = "data"
MODEL_FILENAME = "anomaly_model.pkl"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)
LOG_FILE_PATH = os.path.join(MODEL_DIR, "performance_log.csv")

# --- 1. GENERATE / LOAD HISTORICAL DATA ---
if not os.path.exists(LOG_FILE_PATH) or os.path.getsize(LOG_FILE_PATH) < 100:
    # If log file is missing or too small, generate simulated data for initial training
    np.random.seed(42) 
    # Normal Data (in milliseconds): centered around 300ms
    normal_latency = np.random.normal(loc=300, scale=50, size=1000)
    # Anomalous Data: 20 points (simulating slow responses)
    outliers = np.random.uniform(low=850, high=1200, size=20)
    
    latency_data = np.concatenate([normal_latency, outliers]).reshape(-1, 1)
    df = pd.DataFrame(latency_data, columns=['latency_ms'])
    print("Warning: Training on simulated data. Run agent often to build real data.")
else:
    # Load actual historical data for retraining
    df = pd.read_csv(LOG_FILE_PATH)
    # We focus only on the latency column for this simple model
    df = df[['latency_ms']].copy() 
    print(f"Loading {len(df)} historical data points for retraining.")

# --- 2. TRAIN THE ISOLATION FOREST MODEL ---
# Calculate contamination: estimate 2% of the total dataset are anomalies
contamination_rate = 0.02 
if len(df) > 500: # Adjust contamination only if enough data is present
     contamination_rate = np.clip((len(df[df['latency_ms'] > 800]) / len(df)), 0.005, 0.05)


iso_forest = IsolationForest(
    n_estimators=100, 
    contamination=contamination_rate,
    random_state=42,
    verbose=0
)

# CRITICAL FIX: Fit on the raw NumPy array (.values), NOT the DataFrame, 
# to avoid the feature name mismatch warning during prediction.
iso_forest.fit(df[['latency_ms']].values) 
print(f"Isolation Forest model trained with contamination rate: {contamination_rate:.4f}")

# --- 3. SAVE THE TRAINED MODEL (PICKLE) ---
os.makedirs(MODEL_DIR, exist_ok=True) 

with open(MODEL_PATH, 'wb') as file:
    pickle.dump(iso_forest, file)

print(f"\n✅ Model successfully saved to {MODEL_PATH}")