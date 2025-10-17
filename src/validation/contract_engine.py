# src/validation/contract_engine.py
import json
from deepdiff import DeepDiff
from typing import Dict, Any, List, Union

def _get_comparison_sample(data: Dict[str, Any]) -> Union[Dict[str, Any], List[Any]]:
    """
    Dynamically extracts the most stable, representative sample structure 
    from the API response for comparison.
    """
    # 1. Check for standard array wrapping (e.g., {"data": [...]})
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and data["data"]:
        # If it's a list and has at least one item, use the FIRST item as the contract sample.
        return data["data"][0]
        
    # 2. Check for simple list response (less common, but safe)
    if isinstance(data, list) and data:
        return data[0]

    # 3. If it's a non-list object (e.g., {"success": true, "offerId": "..."}), use the whole thing.
    return data


def get_regression_diff(lsr_data: dict, current_data: dict) -> dict:
    """
    Compares the LSR structure against the current API response.
    
    FAILURE: Triggered only by MISSING KEYS or TYPE CHANGES (backward compatibility breaks).
    WARNING: Triggered by ALL other changes (value change, key added).
    """
    
    lsr_response = lsr_data.get("latest_successful_response", {})
    
    # CRITICAL FIX: Dynamically sample the data for comparison
    lsr_data_sample = _get_comparison_sample(lsr_response)
    current_data_sample = _get_comparison_sample(current_data)
    
    # --- 1. Perform Deep Diff Comparison (Capture EVERYTHING) ---
    full_diff = DeepDiff(
        lsr_data_sample,
        current_data_sample,
        ignore_order=True,
    )
    
    # --- 2. Check for Critical Failure (MISSING KEYS / TYPE CHANGES) ---
    critical_errors = {}
    all_remaining_changes = full_diff.copy() 

    # Check 1: Key Removal (The DEFINITIVE BREAKING CHANGE)
    if 'dictionary_item_removed' in full_diff:
        critical_errors['MISSING_KEYS'] = full_diff['dictionary_item_removed']
        all_remaining_changes.pop('dictionary_item_removed')
    
    # Check 2: Type Changes (Also a breaking change, as code expects a specific type)
    if 'type_changes' in full_diff:
        critical_errors['TYPE_CHANGES'] = full_diff['type_changes']
        all_remaining_changes.pop('type_changes')
        
    # --- 3. Determine Final Status and Report ---
    
    if critical_errors:
        return {
            "status": "FAIL",
            "reason": "CRITICAL_KEY_MISSING_BACKWARD_COMPATIBILITY_BREAK",
            "critical_diff": critical_errors,
            "all_other_changes": all_remaining_changes 
        }
    elif full_diff:
        # Status is PASS_WITH_WARNING if only additions or non-critical value changes occurred
        return {
            "status": "PASS_WITH_WARNING",
            "reason": "STRUCTURAL_OR_VALUE_DRIFT_DETECTED",
            "all_changes": full_diff
        }

    return {"status": "PASS", "reason": "Contract audit passed with zero deviation.", "all_changes": {}}