# 🤖 Diffy - API Contract Regression Validator

An AI-Augmented Quality Engineering tool designed to prevent breaking changes in microservice APIs and monitor for performance anomalies within the CI/CD pipeline.

Diffy enforces **strict backward compatibility** by comparing the current API response structure against a known-good **Latest Successful Response (LSR)** contract. It integrates **Machine Learning (ML)** to identify statistically anomalous latency.

## 🌟 Key Features

* **Deterministic Validation:** Uses `deepdiff` to audit the entire JSON response structure, failing the build if mandatory keys are **missing** or **removed** (a breaking contract change)
* **Probabilistic Validation:** Integrates a trained **ML model** to detect if the current API latency is statistically slower than the historical baseline
* **Automated Patching:** Generates patch files to update contracts when needed
* **Dynamic Discovery:** Automatically processes all contract files in the `contracts/` directory

## 🛠️ Prerequisites

* Python 3.8+
* Required dependencies (see Installation)

## 🚀 Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd diffy

# 2. Create and activate virtual environment (optional)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train the anomaly detection model
python utils/train_anomaly_model.py
```

## 📊 Usage

### Running Contract Validation

```bash
# Validate all contracts
python -m src.main

# Validate a specific contract (full path)
python -m src.main contracts/offer_LSR.json

# Validate a specific contract (simplified)
python -m src.main offer_LSR.json
```

### Fixing Issues

When breaking changes are detected, apply fixes with:
```bash
python patch_contract.py offer_LSR.json
```

## 📁 Project Structure

- `contracts/`: Contains LSR contract files
- `contracts_patch/`: Contains generated patch files
- `data/`: Contains ML model and performance logs
- `reports_output/`: Contains temporary CR files
- `src/`: Source code
  - `validation/`: Contract validation logic
  - `utils/`: Utility functions
  - `tools.py`: API interaction tools
  - `main.py`: Main execution script