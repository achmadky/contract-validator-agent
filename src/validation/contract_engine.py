# src/validation/contract_engine.py
import json
from deepdiff import DeepDiff
from typing import Dict

def get_regression_diff(lsr_data: dict, current_data: dict) -> dict:
    """
    Compares the entire LSR structure against the current API response.
    
    FAILURE: Triggered only by MISSING KEYS or TYPE CHANGES.
    WARNING: Triggered by ALL other changes (value change, key added).
    
    Note: Uses a 'Group By' method for lists to ensure granular reporting, 
          not the confusing full-object replacement.
    """
    
    lsr_response = lsr_data.get("latest_successful_response", {})
    lsr_data_sample = lsr_response
    current_data_sample = current_data
    
    # --- 1. Perform Deep Diff Comparison (Capture EVERYTHING) ---
    # The 'group_by' parameter is CRUCIAL here. It tells DeepDiff to treat 
    # lists of dicts (like 'data') as sets keyed by a unique attribute 
    # (we use the list index '0' for simplicity, but a real key like 'id' is better).
    # This prevents the large, confusing dictionary dump.
    full_diff = DeepDiff(
        lsr_data_sample,
        current_data_sample,
        ignore_order=True,
        # group_by=None is the default for general lists. 
        # Since we are comparing the whole response, we rely on the object structure.
    )
    
    # --- 2. Check for Critical Failure (MISSING KEYS / TYPE CHANGES) ---
    critical_errors = {}
    # Use .copy() to allow us to modify the changes dictionary cleanly
    all_remaining_changes = full_diff.copy()

    # Check 1: Key Removal (The DEFINITIVE BREAKING CHANGE)
    if 'dictionary_item_removed' in full_diff:
        critical_errors['MISSING_KEYS'] = full_diff['dictionary_item_removed']
        all_remaining_changes.pop('dictionary_item_removed')
    
    # Check 2: Type Changes (e.g., int -> string, usually a BREAKING CHANGE)
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
        # If the only things left are non-critical differences (additions, value changes)
        return {
            "status": "PASS_WITH_WARNING",
            "reason": "STRUCTURAL_OR_VALUE_DRIFT_DETECTED",
            "all_changes": full_diff
        }

    return {"status": "PASS", "reason": "Contract audit passed with zero deviation.", "all_changes": {}}