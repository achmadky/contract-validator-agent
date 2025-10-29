#!/usr/bin/env python3
"""
Contract Validation Report Generator

This script validates API contracts against their latest successful responses,
checks for performance anomalies, and generates HTML reports.

Usage:
    python generate_contract_reports.py
"""
import os
import json
import time
import glob
from typing import Dict, Any, List

from src.utils.html_reporter import HTMLReporter
from src.validation.contract_engine import get_regression_diff, _get_comparison_sample
from src.validation.ml_detector import load_anomaly_model, check_performance_anomaly, calculate_normal_range
from src.tools import call_current_api, load_lsr_contract
from src.utils.logger import load_historical_data_for_endpoint

REPORTS_DIR = os.path.join("reports")
ANOMALY_MODEL_PATH = os.path.join("data", "anomaly_model.pkl")


def run_for_contract(contract_path: str) -> Dict[str, Any]:
    """
    Validate a single contract and return the results.
    
    Args:
        contract_path: Path to the contract JSON file
        
    Returns:
        Dictionary with validation results and performance data
    """
    name = os.path.basename(contract_path)
    lsr_data = load_lsr_contract(contract_path)
    target_url = lsr_data["api_contract_meta"]["target_url"]

    # Call API and measure latency
    current_response, current_latency = call_current_api(lsr_data, target_url)

    # Deterministic validation
    regression_diff = get_regression_diff(lsr_data, current_response)

    # Prepare samples for inline diff visualization
    lsr_sample = _get_comparison_sample(lsr_data.get("latest_successful_response", {}))
    current_sample = _get_comparison_sample(current_response)

    # Probabilistic performance check
    anomaly_model = load_anomaly_model(ANOMALY_MODEL_PATH)
    historical_df = load_historical_data_for_endpoint(lsr_data)
    min_range_s, max_range_s = calculate_normal_range(anomaly_model, historical_df)
    is_anomaly = check_performance_anomaly(anomaly_model, current_latency * 1000)

    performance = {
        "is_anomaly": is_anomaly,
        "current_latency": current_latency,
        "min_range": min_range_s,
        "max_range": max_range_s,
    }

    return {
        "contract_name": name,
        "validation_results": regression_diff,
        "performance_data": performance,
        "lsr_sample": lsr_sample,
        "current_sample": current_sample,
    }


def main():
    """
    Main function to validate all contracts and generate reports.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    reporter = HTMLReporter(output_dir=REPORTS_DIR)

    # Find contracts to run (json files under contracts/, prefer *_LSR.json)
    contracts_dir = os.path.join("contracts")
    items: List[Dict[str, Any]] = []
    
    # Track execution statistics
    stats = {
        "total": 0,
        "pass": 0,
        "pass_with_warning": 0,
        "fail": 0,
        "unknown": 0,
        "errors": 0,
        "breaking_changes": 0,
        "perf_anomalies": 0
    }
    
    for path in glob.glob(os.path.join(contracts_dir, "*_LSR.json")):
        stats["total"] += 1
        try:
            result = run_for_contract(path)
            items.append(result)
            
            # Update statistics based on validation status
            status = result["validation_results"].get("status", "UNKNOWN")
            if status == "PASS":
                stats["pass"] += 1
            elif status == "PASS_WITH_WARNING":
                stats["pass_with_warning"] += 1
            elif status == "FAIL":
                stats["fail"] += 1
            else:
                stats["unknown"] += 1
            
            # Track breaking changes
            if result["validation_results"].get("critical_diff"):
                stats["breaking_changes"] += 1
                
            # Track performance anomalies
            if result["performance_data"].get("is_anomaly"):
                stats["perf_anomalies"] += 1
                
            # Generate per-contract report
            reporter.generate_report(
                result["contract_name"],
                result["validation_results"],
                result["performance_data"],
                result.get("lsr_sample"),
                result.get("current_sample"),
            )
        except Exception as e:
            stats["errors"] += 1
            print(f"Error running {os.path.basename(path)}: {type(e).__name__}: {e}")

    # Generate aggregate report with dropdown per contract
    agg_path = reporter.generate_aggregate_report(items)
    
    # Print execution summary to console
    print("\n" + "="*50)
    print("EXECUTION SUMMARY")
    print("="*50)
    print(f"Total contracts processed: {stats['total']}")
    print(f"PASS: {stats['pass']}")
    print(f"PASS with value changes: {stats['pass_with_warning']}")
    print(f"Broken: {stats['fail']}")
    print(f"UNKNOWN: {stats['unknown']}")
    print(f"Breaking changes detected: {stats['breaking_changes']}")
    print(f"Performance anomalies: {stats['perf_anomalies']}")
    print(f"Errors during execution: {stats['errors']}")
    print("="*50)
    print(f"Aggregate report generated at: {agg_path}")
    print(f"You can open this file directly in your browser.")


if __name__ == "__main__":
    main()