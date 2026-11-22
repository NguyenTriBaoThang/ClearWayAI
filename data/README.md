# ClearWayAI Data Subsystem (`data`)

Houses synthetic seed fixtures, dataset annotations, and data governance manifests.

---

## 1. Directory Structure

```
data/
├── seed/                   # Seed fixtures labeled DEMO_FIXTURE for offline UI testing
├── raw/                    # Raw video clips and telemetry (governed by privacy scrub policy)
├── processed/              # Formatted YOLO / COCO annotations and clearance time tables
└── README.md
```

---

## 2. Privacy & Video Governance

- **Zero PII Policy:** All raw video inputs undergo automated face and license plate blurring.
- **Scene-Based Splits:** Datasets are partitioned strictly by intersection scene and recording day to prevent temporal leakage across adjacent frames.
- **Data Provenance:** Every sample file is labeled with its origin (`DEMO_FIXTURE`, `SUMO_SIMULATED`, `OFFLINE_VIDEO`, `SHADOW_ADVISORY`, or `LIVE_CONNECTED`).

