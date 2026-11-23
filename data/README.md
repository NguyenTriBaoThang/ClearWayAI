# ClearWayAI Data Subsystem (`data`)

Houses synthetic seed fixtures, dataset manifests, privacy scrubber pipelines, and data governance frameworks compliant with Vietnam's Decree 13/2023/ND-CP.

---

## 1. Directory Structure

```
data/
├── manifests/              # Immutable JSON metadata manifests with SHA-256 digests
│   ├── manifest_hcmc_d1_peak.json       # HCMC D1 morning peak (76.5% motorcycles)
│   ├── manifest_hcmc_d5_rain.json       # HCMC D5 evening rain & wet reflections
│   ├── manifest_hanoi_night.json        # Hanoi Hoan Kiem nighttime lighting
│   └── manifest_synthetic_corridor.json # Digital twin SUMO corridor ground truth
├── scripts/                # Anonymization & manifest validation utilities
│   ├── anonymize.py          # Decree 13 face & license plate privacy scrubber
│   └── validate_manifests.py # Strict Pydantic JSON manifest validator
├── seed/                   # Seed fixtures labeled DEMO_FIXTURE for offline UI testing
│   └── traffic_fixture.json
├── raw/                    # Raw ingress quarantine (retention <= 14 days)
└── processed/              # Privacy-scrubbed YOLO / ByteTrack annotations
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

### 3.2 Verify Single Manifest Decree 13 Compliance
```bash
python data/scripts/anonymize.py --check-manifest data/manifests/manifest_hcmc_d1_peak.json
```

### 3.3 Compute SHA-256 File Digest
```bash
python data/scripts/anonymize.py --hash data/manifests/manifest_hcmc_d1_peak.json
```
