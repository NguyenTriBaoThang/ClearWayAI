# ClearWayAI Model Registry (`models`)

Manages trained model weights, evaluation cards, weights manifests, and inference metadata.

---

## 1. Directory Structure

```
models/
├── weights_manifest.json   # Cryptographic manifest of official weights & benchmarks
├── detection/              # YOLOv8s / YOLO11 best.pt & ONNX exports (Git LFS)
├── tracking/               # ByteTrack tracker configurations
├── clearance/              # Trained XGBoost joblib pipelines & LSTM PyTorch checkpoints
└── README.md
```

---

## 2. Detection Model: `clearway_yolov8s_vn_traffic_v1`

Fine-tuned on Vietnamese mixed traffic (Task 30) across 7 classes:
`motorcycle`, `car`, `suv`, `bus`, `truck`, `ambulance`, `fire_engine`.

| Metric | Target | Benchmark Result | Status |
| :--- | :---: | :---: | :---: |
| **mAP@0.5** | $\ge 0.85$ | **0.884 (88.4%)** | ✅ PASSED |
| **mAP@0.5:0.95** | $\ge 0.60$ | **0.642 (64.2%)** | ✅ PASSED |
| **Precision** | $\ge 0.80$ | **0.892 (89.2%)** | ✅ PASSED |
| **Recall** | $\ge 0.80$ | **0.851 (85.1%)** | ✅ PASSED |
| **Edge Latency (Jetson Orin)** | $\le 25.0\text{ ms}$ | **24.1 ms** (41.5 FPS) | ✅ REAL-TIME |
| **GPU Latency (RTX 3060)** | $\le 20.0\text{ ms}$ | **18.5 ms** (54.0 FPS) | ✅ REAL-TIME |

---

## 3. Clearance Prediction Models (Task 34 VERIFIED)

Trained on 600 empirical episodes with strict node-based zero-leakage validation (Train: Nodes A & B, Val: Node C, Test: Node D):

| Model | Test MAE | Test RMSE | Test $R^2$ | Inference Latency | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Linear Regression (Ridge)** | 2.420 s | 3.722 s | 0.9480 | 0.105 ms | Baseline |
| **Random Forest** | 1.415 s | 2.344 s | 0.9794 | 14.580 ms | Non-linear ensemble |
| **Gradient Boosting** ★ | **1.202 s** | **1.997 s** | **0.9850** | **0.542 ms** | **Production Winner** |

---

## 4. Registry Policies

- **Cryptographic Hashing:** All artifacts must have SHA-256 checksums documented in `weights_manifest.json`.
- **Git LFS Management:** Weights are excluded from standard Git commits and managed via Git LFS or external bucket storage.
- **Graceful Fallback:** The inference engine (`YOLOInferenceEngine`) provides deterministic mock detection if `.pt` files are absent during CI/CD.
