# patch_contract.py
import json
import os
import sys
import argparse
from deepdiff import DeepDiff
from typing import List, Dict, Any

# --- CONFIGURATION ---
CONTRACTS_DIR = "contracts"
REPORTS_OUTPUT_DIR = "reports_output" # Directory where main.py saves the temporary CR file
PATCH_TARGET_DIR = "contracts_patch" # Directory for saving the review copy
PATCH_FILE_SUFFIX = "_patcher.json"

# --- UTILITY FUNCTIONS ---

def load_json_file(filepath: str) -> dict:
    """Loads a JSON file, raising a clean error if not found or invalid."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at: {filepath}")
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {filepath}")

def delete_temp_cr_file(contract_filename: str):
    """Deletes the temporary Current Response file (CR) created by main.py."""
    base_name = contract_filename.replace('.json', '')
    temp_cr_filename = f"{base_name}_CR.json"
    temp_cr_path = os.path.join(REPORTS_OUTPUT_DIR, temp_cr_filename)
    if os.path.exists(temp_cr_path):
        os.remove(temp_cr_path)
        print(f"   [CLEANUP] Deleted temporary CR file: {temp_cr_filename}")
    else:
        print(f"   [CLEANUP] Temporary CR file not found (Already clean).")

def delete_generated_patch_file(contract_filename: str):
    """Deletes the final generated patch file from the review directory."""
    base_name = contract_filename.replace('.json', '')
    review_filename = f"{base_name}{PATCH_FILE_SUFFIX}"
    review_filepath = os.path.join(PATCH_TARGET_DIR, review_filename)
    if os.path.exists(review_filepath):
        os.remove(review_filepath)
        print(f"   [CLEANUP] Deleted review patch file: {review_filename}")
    # Note: If it doesn't exist, we don't worry, as it was likely already deleted manually.


# --- CORE PATCHING LOGIC ---

def run_patch_audit_for_file(lsr_filepath: str, contract_filename: str):
    """
    Executes the patch logic, attempts to auto-promote the changes, and cleans up.
    """
    
    # 1. Define Paths for Temporary Data
    temp_cr_filename = f"{contract_filename.replace('.json', '')}_CR.json"
    temp_cr_path = os.path.join(REPORTS_OUTPUT_DIR, temp_cr_filename)
    original_lsr_filepath = os.path.join(CONTRACTS_DIR, contract_filename)

    print(f"\n--- Processing Contract: {contract_filename} ---")
    
    try:
        # 2. Check and Load Data: Old Contract and Temporary Live Response (CR)
        if not os.path.exists(temp_cr_path):
            print(f"❌ SKIPPED: Current Response data not found at {temp_cr_path}. Run 'python -m src.main' first.")
            return 1 
            
        old_contract_data = load_json_file(lsr_filepath)
        # CRUCIAL: Load the temporary file which contains {"latest_successful_response": current_response_json}
        cr_wrapper_data = load_json_file(temp_cr_path) 
        
        current_response_data = cr_wrapper_data.get("latest_successful_response", {})
        lsr_response = old_contract_data.get("latest_successful_response", {})

        # 3. Perform Comparison
        full_diff = DeepDiff(lsr_response, current_response_data, ignore_order=True)
        
        # Check for CRITICAL errors (removals/type changes)
        if full_diff.get('dictionary_item_removed') or full_diff.get('type_changes'):
            print("\n❌ CRITICAL: Breaking changes detected. Patching ABORTED.")
            print("Action: Fix the API code. Cannot auto-approve deletions.")
            delete_temp_cr_file(contract_filename)
            return 1 

        # If no changes at all, cleanup and exit.
        if not full_diff:
            print("\n✅ SUCCESS: Contract is structurally identical. No patch file needed.")
            delete_temp_cr_file(contract_filename)
            return 0 

        # 4. CONSTRUCT THE FINAL PATCHED CONTRACT
        
        patched_contract = old_contract_data.copy()
        
        # Overwrite ONLY the 'latest_successful_response' key with the new, live structure
        patched_contract["latest_successful_response"] = current_response_data
        
        # 5. SAVE THE REVIEW COPY and OVERWRITE THE ORIGINAL

        # A. Save review copy (Optional but recommended backup)
        base_name = contract_filename.replace('.json', '')
        review_filename = f"{base_name}{PATCH_FILE_SUFFIX}"
        review_filepath = os.path.join(PATCH_TARGET_DIR, review_filename)
        
        os.makedirs(PATCH_TARGET_DIR, exist_ok=True) 
        with open(review_filepath, 'w') as f:
             json.dump(patched_contract, f, indent=2) 
        
        # B. CRITICAL STEP: Overwrite the original contract file
        with open(original_lsr_filepath, 'w') as f:
            json.dump(patched_contract, f, indent=2)

        # 6. Final Report and Cleanup
        
        print("\n✨ AUTO-PROMOTION SUCCESSFUL!")
        print(f"File {contract_filename} in {CONTRACTS_DIR}/ has been automatically updated.")
        print(f"Patched Changes: {len(full_diff)} difference(s) were adopted.")
        
        # Clean up both temporary files after successful overwrite
        delete_generated_patch_file(contract_filename) 
        delete_temp_cr_file(contract_filename) 

        print("\nACTION REQUIRED: Review changes using 'git diff' and commit the updated contract.")
        
        return 0 

    except Exception as e:
        print(f"\nFATAL UNHANDLED ERROR processing {contract_filename}: {type(e).__name__}: {e}")
        return 1 


# --- Main CLI Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to perform dynamic/mass self-healing on contract files."
    )
    parser.add_argument(
        "contract_filename",
        nargs='?', 
        type=str,
        help="Specific filename to patch (e.g., offers_LSR.json) OR leave blank to patch all contracts."
    )
    
    args = parser.parse_args()
    
    # 1. Determine which files to run
    files_to_patch = []
    
    if args.contract_filename:
        # Specific Execution Mode
        target_filename = args.contract_filename
        full_path = os.path.join(CONTRACTS_DIR, target_filename)
        
        if os.path.exists(full_path) and target_filename.endswith("_LSR.json"):
            files_to_patch = [(full_path, target_filename)]
        else:
            print(f"Error: Specified contract file '{args.contract_filename}' not found or invalid.")
            sys.exit(1)
            
    else:
        # Mass Execution Mode (Run All)
        all_paths = discover_contract_files(CONTRACTS_DIR)
        files_to_patch = [(p, os.path.basename(p)) for p in all_paths]

    if not files_to_patch:
        print("No contracts found to patch. Exiting.")
        sys.exit(0)

    # 2. Execute patching loop
    total_failures = 0
    
    print(f"--- Starting Contract Patching in {'MASS MODE' if not args.contract_filename else 'SPECIFIC MODE'} ---")
    
    for full_path, filename in files_to_patch:
        status_code = run_patch_audit_for_file(full_path, filename)
        if status_code != 0:
            total_failures += 1
            
    # 3. Final Summary
    print("\n=============================================")
    if total_failures > 0:
        print(f"🔴 PATCH PROCESS COMPLETED WITH {total_failures} ERRORS. Check console output.")
    else:
        print("🟢 PATCH PROCESS COMPLETED. All eligible contracts updated successfully.")
    
    sys.exit(total_failures)

if __name__ == "__main__":
    main()