import json
import os
import sys
from typing import List

# Corrected Imports: Assuming these files exist in their respective directories within 'src/'
from .validation.contract_engine import get_regression_diff
from .validation.ml_detector import load_anomaly_model, check_performance_anomaly
from .tools import call_current_api, load_lsr_contract 

# --- CONFIGURATION ---
CONTRACTS_DIR = "contracts"
ANOMALY_MODEL_PATH = os.path.join("data", "anomaly_model.pkl")

# --- 1. File Discovery ---
def discover_contract_files(directory: str) -> List[str]:
    """Finds all JSON files ending with _LSR.json in the contracts directory."""
    full_paths = []
    if not os.path.isdir(directory):
        print(f"Error: Contract directory '{directory}' not found.")
        return []

    for filename in os.listdir(directory):
        if filename.endswith("_LSR.json"):
            full_paths.append(os.path.join(directory, filename))
            
    return full_paths

# --- 2. Main Execution Loop ---
def run_contract_validation_agent():
    
    # 2.1 Load ML Model (Required for Probabilistic Check)
    contract_files = discover_contract_files(CONTRACTS_DIR)

    try:
        anomaly_model = load_anomaly_model(ANOMALY_MODEL_PATH) 
    except FileNotFoundError:
        print(f"FATAL ERROR: ML model not found. Please run 'python utils/train_anomaly_model.py' first.")
        sys.exit(1)
        
    overall_fail_count = 0
    
    # 2.2 Iterate through all discovered contracts
    if not contract_files:
        print("No contract files found. Exiting gracefully.")
        sys.exit(0)

    for lsr_file_path in contract_files:
        
        try:
            lsr_data = load_lsr_contract(lsr_file_path)
            target_url = lsr_data["api_contract_meta"]["target_url"]
            contract_name = os.path.basename(lsr_file_path)
            
            print(f"\n--- Running Contract: {contract_name} ---")
            print(f"--- Target URL: {target_url} ---")
            
            # --- DETERMINISTIC CHECK ---
            current_response, current_latency = call_current_api(target_url) 
            regression_diff = get_regression_diff(lsr_data, current_response)
            
            final_status = regression_diff.get("status", "PASS") 
            
            # --- DIRECT REPORTING (Deterministic Result) ---
            print("\n[DETERMINISTIC VALIDATION AUDIT]")
            
            if final_status == "FAIL":
                overall_fail_count += 1
                critical_diff = regression_diff.get('critical_diff', {})
                all_other_changes = regression_diff.get("all_other_changes", {}) # Non-critical changes
                
                print(f"❌ STATUS: FAILED (CRITICAL REGRESSION)")
                print(f"   Reason: {regression_diff.get('reason')}")
                
                # 1. Report Missing Keys (Critical)
                missing_keys = critical_diff.get('MISSING_KEYS', {})
                if missing_keys:
                    print("\n--- 🚨 CRITICAL ERROR: MISSING PARAMETERS (BREAKING CHANGE) ---")
                    # FIX: Iterate directly over the SetOrdered object (for parameter path)
                    for path in missing_keys: 
                        print(f"   🚨 PARAMETER REMOVED: {path}. Was expected in LSR but not found in current response.") 
                
                # 2. Report Type Changes (Critical)
                if 'TYPE_CHANGES' in critical_diff:
                    print("\n--- 🚨 CRITICAL ERROR: TYPE CHANGE ---")
                    print(f"   Details: {json.dumps(critical_diff['TYPE_CHANGES'], indent=2)}")

                # 3. Report Other Non-Critical Changes (User Request: Show all diffs)
                if all_other_changes:
                    print("\n--- ⚠️ SOFT WARNINGS (Concurrent Non-Breaking Changes) ---")
                    
                    # 3a. Report Keys Added (Non-breaking but new)
                    if 'dictionary_item_added' in all_other_changes:
                        print("🟢 KEYS ADDED:")
                        for path in all_other_changes['dictionary_item_added']:
                            print(f"   + PARAMETER ADDED: {path}")

                    # 3b. Report Value Changes (Soft change)
                    if 'values_changed' in all_other_changes:
                        print("\n🟡 VALUE CHANGES:")
                        for path, details in all_other_changes['values_changed'].items():
                            print(f"   ~ PARAMETER VALUE CHANGED: {path}")
                            print(f"     Old Value: {details.get('old_value')}")
                            print(f"     New Value: {details.get('new_value')}")
                            
                    # 3c. Report other structural changes (if any remain)
                    remaining_keys = [k for k in all_other_changes if k not in ['dictionary_item_added', 'values_changed']]
                    if remaining_keys:
                        print("\n--- OTHER STRUCTURAL CHANGES (Technical Diff) ---")
                        # Create a subset dictionary for clean printing
                        other_technical_diff = {k: all_other_changes[k] for k in remaining_keys}
                        print(f"{json.dumps(other_technical_diff, indent=2)}") 
            
            elif final_status == "PASS_WITH_WARNING":
                # Non-breaking changes (Additions, safe value changes) are treated as a soft alert.
                print("⚠️ STATUS: PASSED WITH WARNING (Contract Drift)")
                print(f"   Reason: {regression_diff.get('reason')}")
                
                all_changes = regression_diff.get('all_changes', {})
                
                print("\n--- ALL DIFFERENCES FOUND (Requires Audit) ---")
                
                # 1. Report Keys Added (Non-breaking but new)
                if 'dictionary_item_added' in all_changes:
                    print("🟢 KEYS ADDED (Non-Breaking):")
                    for path in all_changes['dictionary_item_added']:
                        print(f"   + PARAMETER ADDED: {path}")

                # 2. Report Value Changes (Soft change)
                if 'values_changed' in all_changes:
                    print("\n🟡 VALUE CHANGES (Soft Difference):")
                    for path, details in all_changes['values_changed'].items():
                        print(f"   ~ PARAMETER VALUE CHANGED: {path}")
                        print(f"     Old Value: {details.get('old_value')}")
                        print(f"     New Value: {details.get('new_value')}")
                        
                # 3. Report other changes captured by DeepDiff 
                if any(key not in ['dictionary_item_added', 'values_changed'] for key in all_changes):
                    print("\n--- OTHER STRUCTURAL CHANGES (Technical Diff) ---")
                    print(f"{json.dumps(all_changes, indent=2)}") 

            else:
                print("✅ STATUS: PASSED (Strict Audit found zero deviation)")


            # --- PROBABILISTIC CHECK (ML Result) ---
            # Model input expects milliseconds, hence we convert seconds to milliseconds
            is_anomaly = check_performance_anomaly(anomaly_model, current_latency * 1000) 
            
            print("\n[PROBABILISTIC VALIDATION]")
            if is_anomaly:
                 print(f"🔴 WARNING: Performance Anomaly Detected!")
                 print(f"   Latency: {current_latency:.4f}s (Statistically abnormal for baseline)")
            else:
                 print(f"🟢 OK: Latency {current_latency:.4f}s is within expected range.")

        except Exception as e:
            # Catch any other runtime error during processing
            print(f"UNEXPECTED ERROR processing {contract_name}: {type(e).__name__}: {e}")
            overall_fail_count += 1

    # --- 3. FINAL EXECUTION RESULT ---
    print("\n=============================================")
    if overall_fail_count > 0:
        print(f"🔴 FINAL BUILD STATUS: FAILED. {overall_fail_count} contract(s) broken.")
        sys.exit(1)
    else:
        print("🟢 FINAL BUILD STATUS: PASSED. All checks complete.")
        sys.exit(0)

if __name__ == "__main__":
    run_contract_validation_agent()