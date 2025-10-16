# src/tools.py
import requests
import json
import os
import time
import random
from typing import Tuple, Dict, Any

def load_lsr_contract(file_path: str) -> Dict:
    """Loads the Latest Successful Response (LSR) from storage."""
    # Note: Assumes file_path is relative to the project root or accessible via CI path
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Raise an explicit error if the contract file is missing
        raise FileNotFoundError(f"LSR Contract file not found at: {file_path}. Did you create it?")

def call_current_api(endpoint_url: str) -> Tuple[Dict[str, Any], float]:
    """
    Calls the live API endpoint, measures real latency, and returns the response body.
    
    Returns:
        tuple: (JSON response body, latency in seconds)
    """
    
    # --- PRODUCTION IMPLEMENTATION ---
    
    start_time = time.time()
    
    try:
        # Use a generous timeout (10 seconds) for external API testing
        response = requests.get(endpoint_url, timeout=10)
        
        # Raise an exception for bad status codes (4xx or 5xx errors)
        response.raise_for_status()
        response_body = response.json()
        
    except requests.exceptions.RequestException as e:
        # If the API is down or returns a severe error, we still measure latency to capture the failure time.
        end_time = time.time()
        latency_sec = end_time - start_time
        
        # Re-raise the error so main.py handles the FATAL failure
        raise Exception(f"API Request Failed ({response.status_code if 'response' in locals() else 'Connection Error'}): {e}")

    end_time = time.time()
    latency_sec = end_time - start_time
    
    return response_body, latency_sec