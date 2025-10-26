# 🤖 Diffy - API Contract Regression Validator

An AI-Augmented Quality Engineering tool designed to prevent breaking changes in microservice APIs and monitor for performance anomalies within the CI/CD pipeline.

Diffy enforces strict backward compatibility by comparing the current API response structure against a known-good Latest Successful Response (LSR) contract. It integrates Machine Learning (ML) to identify statistically anomalous latency.

## 🌟 Key Features

- Deterministic validation: audits JSON structure, detects missing/removed keys and type changes
- Performance anomaly detection: uses a trained ML model against historical latency
- Automated patching: generates patch files to update contracts when appropriate
- Dynamic discovery: processes all `*_LSR.json` contracts under `contracts/`
- HTML reporting: generates per-contract and aggregate reports for easy review

## 🛠️ Prerequisites

- Python 3.8+
- Dependencies in `requirements.txt`

## 🚀 Installation

```bash
# 1) Clone the repository
git clone <repository-url>
cd diffy


# 2) Install dependencies
pip install -r requirements.txt

# 3) Train the anomaly detection model (creates data/anomaly_model.pkl)
python utils/train_anomaly_model.py
```

## 📊 Usage

### Running Contract Validation (CLI)

```bash
# Validate all contracts
python -m src.main

# Validate a specific contract (full path)
python -m src.main contracts/offer_LSR.json

# Validate a specific contract (simplified)
python -m src.main offer_LSR.json
```

### Generating HTML Reports (Recommended)

Use the report generator to produce per-contract reports and an aggregate dashboard in `reports/`.

```bash
python generate_contract_reports.py
```

What it does:
- Scans `contracts/` for files matching `*_LSR.json`
- Calls the live API defined in each contract and measures latency
- Performs deterministic diff against the LSR
- Runs performance anomaly checks using the trained model
- Generates:
  - Per-contract HTML reports: `reports/<contract_name>_<timestamp>.html`
  - Aggregate dashboard: `reports/contracts_aggregate_<timestamp>.html`

### Fixing Issues (Patch Contracts)

When breaking changes are detected, apply fixes and update the contract:

```bash
python patch_contract.py offer_LSR.json
```

## 📁 Project Structure

- `contracts/` — LSR contract files (`*_LSR.json`)
- `contracts_patch/` — Generated patch files
- `data/` — ML model and performance logs
- `reports/` — Generated HTML reports (per-contract and aggregate)
- `reports_output/` — Temporary CR files (used by legacy/main validation flow)
- `src/` — Source code
  - `validation/` — Contract validation logic
  - `utils/` — Utilities (HTML reporter, logging)
  - `tools.py` — API interaction tools
  - `main.py` — CLI validation flow
- `generate_contract_reports.py` — HTML report generator
- `patch_contract.py` — Contract patching tool

## ❓ Troubleshooting

- Ensure `utils/train_anomaly_model.py` was run so `data/anomaly_model.pkl` exists.
- If API calls fail (e.g., auth, network), check `api_contract_meta` in the contract for headers and base URL.
- Contracts must include a `latest_successful_response` block for deterministic comparisons.
- If reports aren’t generated, verify you have read/write permissions to the `reports/` directory.