# utils/train_anomaly_model.py (REVISED for NumPy Consistency)
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os

# --- 1. CONFIGURATION ---
MODEL_DIR = "data"
MODEL_FILENAME = "anomaly_model.pkl"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

# --- 2. GENERATE HISTORICAL DATA ---
np.random.seed(42) 
normal_latency = np.random.normal(loc=0.700, scale=0.050, size=1000) * 1000 
outliers = np.random.uniform(low=0.850, high=1.200, size=20) * 1000 

latency_data = np.concatenate([normal_latency, outliers]).reshape(-1, 1)

# df is used only to create the data, not for fitting (to avoid the feature name bug)
df = pd.DataFrame(latency_data, columns=['latency_ms'])
print(f"Total training data points: {len(df)}")

# --- 3. TRAIN THE ISOLATION FOREST MODEL ---
contamination_rate = len(outliers) / len(df)

iso_forest = IsolationForest(
    n_estimators=100, 
    contamination=contamination_rate,
    random_state=42,
    verbose=0
)

# CRITICAL FIX: Fit on the raw NumPy array (.values), NOT the DataFrame.
# This tells the model: "Do not save feature names."
iso_forest.fit(df[['latency_ms']].values) 
print(f"Isolation Forest model trained with contamination rate: {contamination_rate:.4f}")

# --- 4. SAVE THE TRAINED MODEL (PICKLE) ---
os.makedirs(MODEL_DIR, exist_ok=True) 

with open(MODEL_PATH, 'wb') as file:
    pickle.dump(iso_forest, file)

print(f"\n✅ Model successfully saved to {MODEL_PATH}")