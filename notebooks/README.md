# ClearWayAI Research & Training Notebooks (`notebooks`)

Contains interactive Jupyter and Google Colab notebooks for model exploration, exploratory data analysis, and benchmark plotting.

---

## 1. Directory Structure

```
notebooks/
├── 01_eda_traffic_states.ipynb     # Exploratory analysis of queues and speeds
├── 02_yolo_finetune_colab.ipynb    # YOLO11 fine-tuning on Google Colab GPU
├── 03_clearance_baseline_xgb.ipynb # XGBoost training & SHAP explainability
├── 04_clearance_lstm_sequence.ipynb# PyTorch sequence LSTM training
├── 05_ablation_evaluation.ipynb    # Multi-seed ablation analysis & figure generator
└── README.md
```

---

## 2. Usage Instructions

1. Notebooks are designed to run in both local Jupyter environments and Google Colab with minimal setup.
2. Dependencies required for training are specified in root `requirements.txt`.
3. Model evaluation outputs generated from notebooks are saved directly to `data/processed/` and `models/`.

