# ClearWayAI Model Registry (`models`)

Manages trained model weights, evaluation cards, and inference metadata.

---

## 1. Directory Structure

```
models/
├── detection/              # YOLO11 best.pt & ONNX exports (Git LFS)
├── tracking/               # ByteTrack tracker configurations
├── clearance/              # Trained XGBoost joblib pipelines & LSTM PyTorch checkpoints
└── README.md
```

---

## 2. Registry Policies

- **Cryptographic Hashing:** All artifacts must have SHA256 checksums documented.
- **Model Card Required:** Every model file must be accompanied by a model card following `docs/MODEL_CARD_TEMPLATE.md`.
- **Git LFS Management:** Weights are excluded from standard Git commits and managed via Git LFS or external bucket storage.

