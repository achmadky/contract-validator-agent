import requests # Synchronous library for API calls
import json
import time
from typing import Tuple, Dict, Any

# --- File Loading Utility ---

def load_lsr_contract(file_path: str) -> Dict:
    """Loads the Latest Successful Response (LSR) contract from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Raise an explicit error if the contract file is missing
        raise FileNotFoundError(f"LSR Contract file not found at: {file_path}. Did you create it?")

# --- API Execution Tool (Corrected Signature) ---

def call_current_api(lsr_data: dict, endpoint_url: str) -> Tuple[Dict[str, Any], float]:
    """
    Calls the API endpoint using dynamic request details from the contract.
    
    Args:
        lsr_data: The full loaded contract data containing request details.
        endpoint_url: The target URL (used for the actual call).
        
    Returns:
        tuple: (JSON response body, latency in seconds)
    """
    
    # 1. DYNAMICALLY EXTRACT REQUEST DETAILS FROM LSR
    request_meta = lsr_data.get("api_contract_meta", {})
    details = lsr_data.get("request_details", {})
    
    # Defaults to GET if not specified in the contract
    method = request_meta.get("method", "GET").upper() 
    
    # Safely extracts headers and body (defaults to empty dicts/None)
    headers = details.get("headers", {})
    json_body = details.get("body")
    
    # 2. EXECUTE API CALL AND MEASURE LATENCY
    start_time = time.time()
    response_body = {}
    
    try:
        # Use requests.request() to handle all methods dynamically
        response = requests.request(
            method=method,
            url=endpoint_url,
            headers=headers,
            json=json_body, # Passed for POST/PUT/PATCH (will be None for GET)
            timeout=10 
        )
        
        response.raise_for_status() 
        
        # Attempt to parse response body (handles 204 No Content)
        try:
            response_body = response.json()
        except requests.exceptions.JSONDecodeError:
            response_body = {} 
        
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        latency_sec = end_time - start_time
        
        # Re-raise the error with context for main.py to handle
        status_code = response.status_code if 'response' in locals() else 'Connection Error'
        raise Exception(f"API Request Failed ({method} {endpoint_url} Status: {status_code}): {e}")

    end_time = time.time()
    latency_sec = end_time - start_time
    
    return response_body, latency_sec