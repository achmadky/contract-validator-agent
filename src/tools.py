# src/tools.py
import requests 
import json
import time
import hashlib
from typing import Tuple, Dict, Any

# --- File Loading Utility ---
def load_lsr_contract(file_path: str) -> Dict:
    """Loads the Latest Successful Response (LSR) contract from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"LSR Contract file not found at: {file_path}. Did you create it?")

# --- API Execution Tool (Synchronous Request) ---
def call_current_api(lsr_data: dict, endpoint_url: str) -> Tuple[Dict[str, Any], float]:
    """
    Calls the API endpoint using dynamic request details from the contract.
    """
    
    # 1. DYNAMICALLY EXTRACT REQUEST DETAILS FROM LSR
    request_meta = lsr_data.get("api_contract_meta", {})
    details = lsr_data.get("request_details", {})
    
    method = request_meta.get("method", "GET").upper() 
    headers = details.get("headers", {})
    json_body = details.get("body")
    
    # 2. EXECUTE API CALL AND MEASURE LATENCY
    start_time = time.time()
    response_body = {}
    
    try:
        response = requests.request(
            method=method,
            url=endpoint_url,
            headers=headers,
            json=json_body, 
            timeout=10 
        )
        
        response.raise_for_status() 
        
        try:
            response_body = response.json()
        except requests.exceptions.JSONDecodeError:
            response_body = {} 
        
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        latency_sec = end_time - start_time
        
        status_code = response.status_code if 'response' in locals() else 'Connection Error'
        raise Exception(f"API Request Failed ({method} {endpoint_url} Status: {status_code}): {e}")

    end_time = time.time()
    latency_sec = end_time - start_time
    
    return response_body, latency_sec