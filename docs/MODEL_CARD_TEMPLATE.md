# Model Card Template: [Model Name]

---

## 1. Model Details
- **Model Name:** `clearway-[task]-[variant]` (e.g. `clearway-clearance-xgb-v1`)
- **Version:** `1.0.0`
- **Architecture / Framework:** [e.g. XGBoost Regressor, PyTorch 2-layer LSTM, Ultralytics YOLO11s]
- **Training Dataset ID:** `DS-TRAFFIC-XXX`
- **Weights File & SHA256:** `[filename.pt]` (`[sha256 hash]`)
- **Status:** `EXPERIMENTAL` | `VERIFIED_SIM` | `REJECTED`

---

## 2. Intended Use & Safety Scope
- **Primary Application:** Predicts clearance duration for the corridor queue in SUMO microscopic simulation.
- **Out-of-Scope Use:** Direct actuation of real-world public roadside controllers.
- **Fail-Safe Mechanism:** When input confidence is `< 0.70` or inputs are out-of-distribution (OOD), fallback to conservative static buffer calculations.

---

## 3. Evaluation Metrics & Benchmarks
- **Primary Metrics:**
  - Mean Absolute Error (MAE): XX seconds
  - Root Mean Squared Error (RMSE): XX seconds
  - Coefficient of Determination ($R^2$): XX
  - 90th Percentile Error ($p_{90}$): XX seconds
- **Stratified Performance:**
  - Heavy Motorcycle Traffic (> 70%): MAE = XXs
  - Low Motorcycle Traffic (< 40%): MAE = XXs
  - Spillback / Heavy Congestion: MAE = XXs
