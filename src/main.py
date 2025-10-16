import json
import os
import sys
from typing import List

# Corrected Imports
from .validation.contract_engine import get_regression_diff
from .validation.ml_detector import load_anomaly_model, check_performance_anomaly, calculate_normal_range
from .tools import call_current_api, load_lsr_contract 
from .utils.logger import log_performance_data, load_historical_data_for_endpoint 

# --- CONFIGURATION ---
CONTRACTS_DIR = "contracts"
ANOMALY_MODEL_PATH = os.path.join("data", "anomaly_model.pkl") 
REPORTS_OUTPUT_DIR = "reports_output" # Directory where temporary files are saved
PATCH_TARGET_DIR = "contracts_patch" # Directory where final patch files are saved

# --- 1. File Discovery (Remains the same) ---
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
def run_contract_validation_agent(contract_files: List[str]):
    
    # 2.1 Load ML Model
    try:
        anomaly_model = load_anomaly_model(ANOMALY_MODEL_PATH) 
    except FileNotFoundError:
        print(f"FATAL ERROR: ML model not found. Please run 'python utils/train_anomaly_model.py' first.")
        sys.exit(1)
        
    overall_fail_count = 0
    
    if not contract_files:
        print("No contracts found to run. Exiting gracefully.")
        sys.exit(0)
    
    # Prepare the output directory for temporary files
    os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
    os.makedirs(PATCH_TARGET_DIR, exist_ok=True)

    for lsr_file_path in contract_files:
        
        # Initialize loop-specific variables
        contract_name = os.path.basename(lsr_file_path)
        base_name = contract_name.replace('.json', '')
        
        # CORRECT PATH: Temporary CR file goes into REPORTS_OUTPUT_DIR
        temp_cr_filename = f"{base_name}_CR.json"
        temp_cr_path = os.path.join(REPORTS_OUTPUT_DIR, temp_cr_filename) 
        
        # --- NEW: CHECK FOR EXISTING PATCH FILE (Skip Logic) ---
        patch_filename = f"{base_name}_patcher.json"
        patch_filepath = os.path.join(PATCH_TARGET_DIR, patch_filename)
        
        if os.path.exists(patch_filepath):
            print(f"\n--- SKIPPED: {contract_name} ---")
            print(f"⚠️ Warning: Patch file already exists in {PATCH_TARGET_DIR}. Delete it to re-run the audit.")
            continue
        
        try:
            lsr_data = load_lsr_contract(lsr_file_path)
            target_url = lsr_data["api_contract_meta"]["target_url"]
            
            print(f"\n=============================================")
            print(f"CONTRACT AUDIT: {contract_name}")
            print(f"URL: {target_url}")
            print("=============================================")

            # --- API EXECUTION & LATENCY MEASUREMENT ---
            current_response, current_latency = call_current_api(lsr_data, target_url) 
            
            # 🚨 LOG PERFORMANCE DATA (Feedback Loop)
            log_performance_data(lsr_data, current_latency) 
            
            # --- DETERMINISTIC CHECK ---
            regression_diff = get_regression_diff(lsr_data, current_response)
            final_status = regression_diff.get("status", "PASS") 
            
            # --- ML ANALYSIS (Performance Check) ---
            historical_df = load_historical_data_for_endpoint(lsr_data)
            min_range_s, max_range_s = calculate_normal_range(anomaly_model, historical_df)
            is_anomaly = check_performance_anomaly(anomaly_model, current_latency * 1000) 
            
            # --- CONDITIONAL CR FILE CREATION LOGIC ---
            if final_status != "PASS":
                # Only create the temporary CR file if there is a FAIL or WARNING status
                cr_wrapper_data = {"latest_successful_response": current_response}
                with open(temp_cr_path, 'w') as f:
                    json.dump(cr_wrapper_data, f, indent=2)
            
            # --- START REPORTING BLOCK ---
            
            print("\n[DETERMINISTIC VALIDATION AUDIT]")
            
            if final_status == "FAIL":
                overall_fail_count += 1
                critical_diff = regression_diff.get('critical_diff', {})
                all_other_changes = regression_diff.get("all_other_changes", {})
                
                print(f"❌ STATUS: FAILED (CRITICAL REGRESSION)")
                print(f"   Reason: {regression_diff.get('reason')}")
                
                # 1. Report Missing Keys (Critical)
                missing_keys = critical_diff.get('MISSING_KEYS', {})
                if missing_keys:
                    print("\n--- 🚨 BREAKING CHANGE: PARAMETERS REMOVED ---")
                    for path in missing_keys: 
                        print(f"   🚨 PARAMETER REMOVED: {path}. Was expected in LSR but not found in current response.") 
                
                # 2. Report Type Changes (Critical)
                if 'TYPE_CHANGES' in critical_diff:
                    print("\n--- 🚨 CRITICAL ERROR: TYPE CHANGE ---")
                    print(f"   Details: {json.dumps(critical_diff['TYPE_CHANGES'], indent=2)}")

                # 3. Report Other Non-Critical Changes 
                if all_other_changes:
                    print("\n--- ⚠️ SOFT WARNINGS (Concurrent Non-Breaking Changes) ---")
                    
                    if 'dictionary_item_added' in all_other_changes:
                        print("🟢 KEYS ADDED:")
                        for path in all_other_changes['dictionary_item_added']:
                            print(f"   + PARAMETER ADDED: {path}")

                    if 'values_changed' in all_other_changes:
                        print("\n🟡 VALUE CHANGES:")
                        for path, details in all_other_changes['values_changed'].items():
                            print(f"   ~ PARAMETER VALUE CHANGED: {path}")
                            print(f"     Old Value: {json.dumps(details.get('old_value'))}") 
                            print(f"     New Value: {json.dumps(details.get('new_value'))}") 
                            
                    remaining_keys = [k for k in all_other_changes if k not in ['dictionary_item_added', 'values_changed']]
                    if remaining_keys:
                        print("\n--- OTHER STRUCTURAL CHANGES (Technical Diff) ---")
                        other_technical_diff = {k: all_other_changes[k] for k in remaining_keys}
                        print(f"{json.dumps(other_technical_diff, indent=2)}") 
                
                # Provide fix command after a FAIL
                print(f"\n💡 ACTION: Run 'python patch_contract.py {contract_name}' to apply fixes locally.")
            
            elif final_status == "PASS_WITH_WARNING":
                print("⚠️ STATUS: PASSED WITH WARNING (Contract Drift)")
                print(f"   Reason: {regression_diff.get('reason')}")
                
                all_changes = regression_diff.get('all_changes', {})
                
                print("\n--- ALL DIFFERENCES FOUND (Requires Audit) ---")
                
                if 'dictionary_item_added' in all_changes:
                    print("🟢 KEYS ADDED (Non-Breaking):")
                    for path in all_changes['dictionary_item_added']:
                        print(f"   + PARAMETER ADDED: {path}")

                if 'values_changed' in all_changes:
                    print("\n🟡 VALUE CHANGES (Soft Difference):")
                    for path, details in all_changes['values_changed'].items():
                        print(f"   ~ PARAMETER VALUE CHANGED: {path}")
                        print(f"     Old Value: {json.dumps(details.get('old_value'))}")
                        print(f"     New Value: {json.dumps(details.get('new_value'))}")
                        
                if any(key not in ['dictionary_item_added', 'values_changed'] for key in all_changes):
                    print("\n--- OTHER STRUCTURAL CHANGES (Technical Diff) ---")
                    print(f"{json.dumps(all_changes, indent=2)}")
                    
                # Provide fix command after a WARNING
                print(f"\n💡 ACTION: Run 'python patch_contract.py {contract_name}' to apply additions locally.")

            else:
                print("✅ STATUS: PASSED (Strict Audit found zero deviation)")


            # --- PROBABILISTIC (ML) REPORT ---
            print("\n[PROBABILISTIC VALIDATION]")
            print(f"   Learned Normal Range: {min_range_s:.4f}s to {max_range_s:.4f}s")
            
            if is_anomaly:
                 print(f"🔴 WARNING: Performance Anomaly Detected!")
                 print(f"   Latency: {current_latency:.4f}s (EXCEEDS the learned range).")
            else:
                 print(f"🟢 OK: Latency {current_latency:.4f}s is within expected range.")
            
            print("---------------------------------------------") 

        except Exception as e:
            # Clean up the temporary file on error before exiting loop
            if os.path.exists(temp_cr_path):
                os.remove(temp_cr_path)
            print(f"❌ FATAL ERROR processing {contract_name}: {type(e).__name__}: {e}")
            overall_fail_count += 1
            print("---------------------------------------------")

    # --- 3. FINAL EXECUTION RESULT ---
    print("\n=============================================")
    if overall_fail_count > 0:
        print(f"🔴 FINAL BUILD STATUS: FAILED. {overall_fail_count} contract(s) broken.")
        sys.exit(1)
    else:
        print("🟢 FINAL BUILD STATUS: PASSED. All checks complete.")
        sys.exit(0)

if __name__ == "__main__":
    
    files_to_run = []
    
    if len(sys.argv) > 1:
        # User provided a file name/path argument (Specific Execution)
        arg_path = sys.argv[1]
        
        if os.path.exists(arg_path) and arg_path.endswith("_LSR.json"):
            files_to_run = [arg_path]
        else:
            full_path = os.path.join(CONTRACTS_DIR, arg_path)
            if os.path.exists(full_path):
                files_to_run = [full_path]
            else:
                print(f"Error: Specified contract file '{arg_path}' not found in the {CONTRACTS_DIR} directory.")
                sys.exit(1)
    else:
        # No argument provided: Run all contracts (Discovery Mode)
        files_to_run = discover_contract_files(CONTRACTS_DIR)

    if not files_to_run:
        print("No contracts found to run. Exiting.")
        sys.exit(0)

    run_contract_validation_agent(files_to_run)