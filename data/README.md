# ClearWayAI Data Subsystem (`data`)

Houses synthetic seed fixtures, dataset manifests, privacy scrubber pipelines, YOLO annotation datasets, and data governance frameworks compliant with Vietnam's Decree 13/2023/ND-CP.

---

## 1. Directory Structure

```
data/
├── calibration/            # 4-point Planar Homography calibration profiles
│   ├── cam_hcmc_d1.json         # HCMC D1 (14m x 80m approach ground plane)
│   ├── cam_hcmc_d5.json         # HCMC D5 (16m x 75m approach ground plane)
│   ├── cam_hanoi_hk.json        # Hanoi Hoan Kiem (12m x 70m approach ground plane)
│   └── cam_synth_corridor.json  # Digital Twin corridor approach profile
├── manifests/              # Immutable JSON metadata manifests with SHA-256 digests
│   ├── manifest_hcmc_d1_peak.json       # HCMC D1 morning peak (76.5% motorcycles)
│   ├── manifest_hcmc_d5_rain.json       # HCMC D5 evening rain & wet reflections
│   ├── manifest_hanoi_night.json        # Hanoi Hoan Kiem nighttime lighting
│   └── manifest_synthetic_corridor.json # Digital twin SUMO corridor ground truth
├── splits/                 # Zero temporal/spatial leakage dataset splits
│   └── splits.json         # Disjoint scene & camera partition metadata
├── processed/
│   └── yolo/               # YOLOv8 / YOLOv11 dataset format (7 vehicle classes)
│       ├── dataset.yaml    # Dataset paths, nc=7, class names
│       ├── images/         # [train, val, test]
│       └── labels/         # [train, val, test] normalized bounding boxes
├── scripts/                # Anonymization, validation & audit utilities
│   ├── anonymize.py             # Decree 13 face & license plate privacy scrubber
│   ├── validate_manifests.py    # Strict Pydantic JSON manifest validator
│   ├── split_dataset.py         # Scene-based zero-leakage dataset partitioner
│   └── check_dataset_leakage.py # Mathematical leakage & label integrity auditor
├── seed/                   # Seed fixtures labeled DEMO_FIXTURE for offline UI testing
│   └── traffic_fixture.json
└── raw/                    # Raw ingress quarantine (retention <= 14 days)
```

---

## 2. Privacy & Video Governance (Decree 13/2023/ND-CP)

ClearWayAI operates under a strict **Zero-PII (Personally Identifiable Information) Invariant**:

- **Mandatory Anonymization:** Every physical video feed (`provenance="OFFLINE_VIDEO"`) must have all human faces and vehicle license plates blurred/redacted prior to model training or persistent storage.
- **Retention Tiers:** Raw unscrubbed footage in `data/raw/` is encrypted and purged within a maximum of **14 calendar days**. Anonymized datasets may be retained indefinitely.
- **Cryptographic Chain of Custody:** Each ingest file is hashed with SHA-256 for both raw quarantine ingress and anonymized delivery.
- **Data Provenance:** Every sample is labeled explicitly:
  - `OFFLINE_VIDEO`: Anonymized physical field camera recording.
  - `SUMO_SIMULATED`: Generated from SUMO / digital twin traffic dynamics.
  - `DEMO_FIXTURE`: Static mock fixture for frontend offline development.
  - `SHADOW_ADVISORY`: Real-time passive observation feed.
  - `LIVE_CONNECTED`: Edge-connected production controller.

---

## 3. Tooling & Validation Usage

### 3.1 Validate All Video Ingestion Manifests
```bash
python data/scripts/validate_manifests.py --manifest-dir data/manifests
```

### 3.2 Audit Dataset for Zero Data Leakage & YOLO Labels
```bash
python data/scripts/check_dataset_leakage.py --splits-json data/splits/splits.json
```

### 3.3 Partition Scenes Without Leakage
```bash
python data/scripts/split_dataset.py --output-splits data/splits/splits.json
```

### 3.4 Verify Single Manifest Decree 13 Compliance
```bash
python data/scripts/anonymize.py --check-manifest data/manifests/manifest_hcmc_d1_peak.json
```

### 3.5 Compute SHA-256 File Digest
```bash
python data/scripts/anonymize.py --hash data/manifests/manifest_hcmc_d1_peak.json
```
