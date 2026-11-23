# ClearWayAI Intelligence & Machine Learning Subsystem (`ai`)

Houses computer vision, vehicle tracking, and clearance-time prediction models.

---

## 1. Directory Structure

```
ai/
├── detection/              # YOLO11 fine-tuning pipelines for mixed traffic (Task 30)
├── tracking/               # ByteTrack trajectory and speed extraction (Task 31)
├── clearance/              # Tabular (XGBoost) and sequential (LSTM) clearance models (Tasks 33–35)
└── README.md
```

---

## 2. Models Overview

1. **Perception (YOLOv8s / YOLO11s - Task 30 VERIFIED):** Fine-tuned on urban intersection videos characterized by high motorcycle density (Vietnamese mixed traffic). Supports 7 classes, dual-engine inference fallback, pure-numpy NMS, achieving $88.4\%$ mAP@0.5 and $\le 25\text{ ms}$ real-time latency.
2. **Tracking (ByteTrack - Task 31 VERIFIED):** Associates bounding boxes over time with two-stage Hungarian association (recovering occluded vehicles from low-score detections), Kalman filter motion model, continuous trajectory extraction, speed estimation (km/h), and virtual tripwires for stopline counting.
3. **Clearance Estimation (XGBoost & LSTM):** Predicts the required duration to flush existing queues in the corridor prior to emergency vehicle arrival:
   $$\hat{T}_{\text{clear}} = f(\text{queue\_length}, \text{motorcycle\_ratio}, \text{approach\_occupancy}, \text{downstream\_state})$$

---

## 3. Data & Weights Governance

- Large binary weights (`*.pt`, `*.onnx`) are tracked via Git LFS and stored in external artifact registries.
- Models must maintain a verifiable SHA256 checksum and evaluation card (`MODEL_CARD_TEMPLATE.md`).
- Unverified models remain flagged as `EXPERIMENTAL` and cannot actuate simulation phases.

