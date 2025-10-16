# 🤖 API Contract Regression Validator Agent (Python)

An AI-Augmented Quality Engineering tool designed to prevent breaking changes in microservice APIs and monitor for performance anomalies within the CI/CD pipeline.

This agent enforces **strict backward compatibility** by comparing the current API response structure against a known-good **Latest Successful Response (LSR)** contract. It integrates **Machine Learning (ML)** to identify statistically anomalous latency.

## 🌟 Project Highlights (AI/ML Focus)

* **Deterministic Validation:** Uses `deepdiff` to audit the entire JSON response structure, failing the build if mandatory keys are **missing** or **removed** (a breaking contract change).
* **Probabilistic Validation:** Integrates a trained **Isolation Forest (ML)** model (`scikit-learn`) to detect if the current API latency is statistically slower than the historical baseline.
* **Dynamic Discovery:** Automatically loops through all contract files in the `contracts/` directory, making the agent reusable for any endpoint without manual configuration.
* **Language Stack:** Python, leveraging industry-standard ML and testing libraries.

## 🛠️ Prerequisites

* Python 3.8+
* A UNIX-like terminal (or Windows Subsystem for Linux/Git Bash)

## 🚀 Getting Started

Follow these steps from the root directory of your project:

### Step 1: Installation

Install the required dependencies using the provided file:

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install core and ML dependencies
pip install -r requirements.txt

# 3. Run the Code
python -m src.main

# Assuming your file is named 'offers_LSR.json'
python -m src.main contracts/offers_LSR.json

# OR, if you are lazy and the file is in the contracts folder:
python -m src.main offers_LSR.json 
```