# src/validation/contract_engine.py (Strict Audit Mode)
import json
from deepdiff import DeepDiff

def get_regression_diff(lsr_data: dict, current_data: dict) -> dict:
    """
    Compares the entire LSR structure against the current API response.
    
    FAILURE: Triggered only by MISSING KEYS.
    WARNING: Triggered by ALL other changes (value change, key added, type change).
    """
    
    lsr_response = lsr_data.get("latest_successful_response", {})
    # Use the first element of 'data' array in LSR for structure comparison
    lsr_data_sample = lsr_response.get("data", [{}])[0]
    current_data_sample = current_data.get("data", [{}])[0]
    
    # --- 1. Perform Deep Diff Comparison (Capture EVERYTHING) ---
    # No exclusions: every single difference will be reported by DeepDiff.
    full_diff = DeepDiff(
        lsr_data_sample,
        current_data_sample,
        ignore_order=True,
    )
    
    # --- 2. Check for Critical Failure (MISSING KEYS) ---
    critical_errors = {}
    
    # Check 1: Key Removal (The DEFINITIVE BREAKING CHANGE)
    if 'dictionary_item_removed' in full_diff:
        # Move the critical errors out of the main diff object
        critical_errors['MISSING_KEYS'] = full_diff.pop('dictionary_item_removed')
    
    # --- 3. Determine Final Status and Report ---
    
    if critical_errors:
        # If any mandatory key is missing, this is an immediate FAIL
        return {
            "status": "FAIL",
            "reason": "CRITICAL_KEY_MISSING_BACKWARD_COMPATIBILITY_BREAK",
            "critical_diff": critical_errors,
            # The rest of the diff (additions, value changes) is left in full_diff
            "all_other_changes": full_diff 
        }
    elif full_diff:
        # If the only things left are changes in values or additions of new keys
        return {
            "status": "PASS_WITH_WARNING",
            "reason": "STRUCTURAL_OR_VALUE_DRIFT_DETECTED",
            # Report the full remaining diff as the warning details
            "all_changes": full_diff
        }

    return {"status": "PASS", "reason": "Contract audit passed with zero deviation.", "all_changes": {}}