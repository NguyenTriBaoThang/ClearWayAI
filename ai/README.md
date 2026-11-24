# ClearWayAI Intelligence & Machine Learning Subsystem (`ai`)

Houses computer vision, vehicle tracking, and clearance-time prediction models.

---

## 1. Directory Structure

```
ai/
├── detection/              # YOLO11 fine-tuning pipelines for mixed traffic (Task 30)
├── tracking/               # ByteTrack trajectory and speed extraction (Task 31)
├── clearance/              # Tabular (XGBoost) and sequential (LSTM) clearance models (Tasks 33–35)
├── rl/                     # Gymnasium corridor environment & PPO Actor-Critic agent (Task 59)
├── localization/           # Camera-to-3D projection, Kalman filtering & digital twin verification (Task 60)
└── README.md
```

---

## 2. Models Overview

1. **Perception (YOLOv8s / YOLO11s - Task 30 VERIFIED):** Fine-tuned on urban intersection videos characterized by high motorcycle density (Vietnamese mixed traffic). Supports 7 classes, dual-engine inference fallback, pure-numpy NMS, achieving $88.4\%$ mAP@0.5 and $\le 25\text{ ms}$ real-time latency.
2. **Tracking (ByteTrack - Task 31 VERIFIED):** Associates bounding boxes over time with two-stage Hungarian association (recovering occluded vehicles from low-score detections), Kalman filter motion model, continuous trajectory extraction, speed estimation (km/h), and virtual tripwires for stopline counting.
3. **Clearance Estimation & Model Registry (Tasks 33–36 VERIFIED — Phase E 100% COMPLETE):** Predicts the required duration to flush existing queues in the corridor prior to emergency vehicle arrival:
   $$\hat{T}_{\text{clear}} = f([s_{t-K+1}, \dots, s_t])$$
   Supported by physics-based shockwave simulator (Task 33), Gradient Boosting tabular models (Task 34), sequence models with $K=5$ history sliding windows (Task 35: ClearanceGRU test MAE $=4.73\text{ s}$, latency $=0.78\text{ ms}$), and Model Registry service (Task 36) with dynamic champion routing (`gradient_boosting` for snapshots, `clearance_gru` for sequences) and multi-tier fail-safe fallbacks (Tier 1 Kinematic Shockwave, Tier 2 Conservative Safe Default $25.0\text{ s}$).
4. **Adaptive Signal Coordination via Reinforcement Learning (PPO - Task 59 VERIFIED):** Trains a deep Actor-Critic policy using Proximal Policy Optimization (PPO) in an isolated Gymnasium-compatible corridor sandbox (`ai/rl/traffic_corridor_env.py`). Incorporates the `SignalSafetyGateway` as a hard real-time safety shield (guaranteeing 0 conflicting green violations), with multi-objective rewards reducing civilian cross-street delay by $2.0\%$ while expediting priority ambulance transit.
5. **Real Camera Video to 3D Digital Twin Localization (Task 60 VERIFIED — Phase J 100% COMPLETE):** Projects 2D bounding boxes into the 3D WebGL Cartesian world coordinate system via Planar Homography ($H$) and constant-velocity Kalman filtering (`ai/localization/camera_to_3d.py`). Achieves $\text{RMSE} = 0.448\text{m}$ (well within the $\le 1.50\text{m}$ spatial error budget), lateral lane deviation of $0.023\text{m}$, and heading error of $0.30^\circ$, fully closing the loop between real perception and 3D digital twin verification.

---

## 3. Data & Weights Governance

- Large binary weights (`*.pt`, `*.onnx`) are tracked via Git LFS and stored in external artifact registries.
- Models must maintain a verifiable SHA256 checksum and evaluation card (`MODEL_CARD_TEMPLATE.md`).
- Unverified models remain flagged as `EXPERIMENTAL` and cannot actuate simulation phases.

