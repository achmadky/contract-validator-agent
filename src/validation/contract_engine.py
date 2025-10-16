# src/validation/contract_engine.py (Strict Audit Mode - FINAL)
import json
from deepdiff import DeepDiff

def get_regression_diff(lsr_data: dict, current_data: dict) -> dict:
    """
    Compares the entire LSR structure against the current API response.
    
    FAILURE: Triggered only by MISSING KEYS.
    WARNING: Triggered by ALL other changes (value change, key added, type change).
    """
    
    lsr_response = lsr_data.get("latest_successful_response", {})
    # Use the first element of 'data' array in LSR for structure comparison (important for lists of objects)
    lsr_data_sample = lsr_response.get("data", [{}])[0]
    current_data_sample = current_data.get("data", [{}])[0]
    
    # --- 1. Perform Deep Diff Comparison (Capture EVERYTHING) ---
    full_diff = DeepDiff(
        lsr_data_sample,
        current_data_sample,
        ignore_order=True,
    )
    
    # --- 2. Check for Critical Failure (MISSING KEYS) ---
    critical_errors = {}
    all_remaining_changes = full_diff.copy() # Start with a full copy

    # Check 1: Key Removal (The DEFINITIVE BREAKING CHANGE)
    if 'dictionary_item_removed' in full_diff:
        # Pop the critical errors out of the full list for clean separation
        critical_errors['MISSING_KEYS'] = full_diff['dictionary_item_removed']
        all_remaining_changes.pop('dictionary_item_removed')
    
    # Check 2: Type Changes (Also a breaking change, as code expects a specific type)
    if 'type_changes' in full_diff:
        critical_errors['TYPE_CHANGES'] = full_diff['type_changes']
        all_remaining_changes.pop('type_changes')
        
    # --- 3. Determine Final Status and Report ---
    
    if critical_errors:
        # Status is FAIL if any required key is missing or type changed
        return {
            "status": "FAIL",
            "reason": "CRITICAL_KEY_MISSING_BACKWARD_COMPATIBILITY_BREAK",
            "critical_diff": critical_errors,
            # The remaining non-critical diffs (additions/safe changes)
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