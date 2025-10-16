# src/main.py (FINAL LLM-EXCLUDED VERSION with Detailed Reporting)
import json
import os
import sys

# Corrected Imports: Importing tools and validation logic
from .validation.contract_engine import get_regression_diff
from .validation.ml_detector import load_anomaly_model, check_performance_anomaly
from .tools import call_current_api, load_lsr_contract 
# Note: The above imports (call_current_api, load_lsr_contract) 
# correctly point to src.tools

# --- CONFIGURATION ---
CONTRACTS_DIR = "contracts"
ANOMALY_MODEL_PATH = os.path.join("data", "anomaly_model.pkl")

# --- 1. File Discovery (Remains the same) ---
def discover_contract_files(directory: str) -> list:
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
                
                print(f"❌ STATUS: FAILED (CRITICAL REGRESSION)")
                print(f"   Reason: {regression_diff.get('reason')}")
                
                # Explicitly list missing keys (the most severe issue)
                missing_keys = critical_diff.get('MISSING_KEYS', {})
                if missing_keys:
                    print("\n--- 🚨 CRITICAL ERROR: MISSING PARAMETERS (BREAKING CHANGE) ---")
                    for path, value in missing_keys.items():
                        # The path is the exact location of the missing parameter
                        print(f"   🚨 PARAMETER REMOVED: {path}. Was expected in LSR but not found.") 
                
                # Display other failures (Type Changes) if they occurred
                if 'TYPE_CHANGES' in critical_diff:
                    print("\n--- TYPE CHANGE ERROR ---")
                    print(f"   Details: {json.dumps(critical_diff['TYPE_CHANGES'], indent=2)}")

                # Display all non-critical changes that happened concurrently
                if regression_diff.get("all_other_changes"):
                    print("\n--- SOFT WARNING: OTHER CONCURRENT CHANGES FOUND ---")
                    print(f"   {json.dumps(regression_diff['all_other_changes'], indent=2)}")
            
            elif final_status == "PASS_WITH_WARNING":
                # Non-breaking changes (Additions, safe value changes) are treated as a soft alert.
                print("⚠️ STATUS: PASSED WITH WARNING (Contract Drift)")
                print(f"   Reason: {regression_diff.get('reason')}")
                print("\n--- ALL DIFFERENCES FOUND (Requires Audit) ---")
                
                # This report now shows key additions and value changes
                print(f"{json.dumps(regression_diff.get('all_changes'), indent=2)}") 

            else:
                print("✅ STATUS: PASSED (Strict Audit found zero deviation)")


            # --- PROBABILISTIC CHECK (ML Result) ---
            # Model input expects milliseconds, hence the conversion factor (1000) is implicitly handled by the model in this context
            is_anomaly = check_performance_anomaly(anomaly_model, current_latency * 1000) 
            
            print("\n[PROBABILISTIC VALIDATION]")
            if is_anomaly:
                 print(f"🔴 WARNING: Performance Anomaly Detected!")
                 print(f"   Latency: {current_latency:.4f}s (Statistically abnormal for baseline)")
            else:
                 print(f"🟢 OK: Latency {current_latency:.4f}s is within expected range.")

        except Exception as e:
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