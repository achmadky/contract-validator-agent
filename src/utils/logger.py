# src/utils/logger.py
import os
import csv
import time
import hashlib
from typing import Dict, Any

# CONFIGURATION
LOG_FILE_PATH = os.path.join("data", "performance_log.csv")
HEADER = ['timestamp', 'endpoint_id', 'latency_ms']

def generate_endpoint_hash(url: str, method: str) -> str:
    """Creates a unique SHA256 ID for the endpoint (Method + URL)."""
    # Use lowercase and encode for consistent hashing
    unique_string = f"{method.upper()}:{url.lower()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

def log_performance_data(lsr_data: Dict, latency_sec: float):
    """
    Appends a new data point to the historical performance log CSV.
    The file is created if it does not exist.
    """
    
    # Extract data required for logging
    target_url = lsr_data["api_contract_meta"]["target_url"]
    method = lsr_data["api_contract_meta"].get("method", "GET").upper()
    
    # 1. Calculate the unique ID and latency (in milliseconds)
    endpoint_id = generate_endpoint_hash(target_url, method)
    latency_ms = latency_sec * 1000  # Convert to milliseconds for ML model
    data_row = [time.time(), endpoint_id, latency_ms]
    
    # 2. Check and write to CSV
    file_exists = os.path.exists(LOG_FILE_PATH)
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True) # Ensure data/ folder exists

    try:
        with open(LOG_FILE_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header only if the file is new or empty
            if not file_exists or os.path.getsize(LOG_FILE_PATH) == 0:
                writer.writerow(HEADER)
                
            writer.writerow(data_row)
            
    except Exception as e:
        print(f"WARNING: Failed to log performance data to CSV: {e}")