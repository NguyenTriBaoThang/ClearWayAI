# Dataset Card Template: [Dataset Name]

---

## 1. Dataset Summary
- **Dataset ID:** `DS-TRAFFIC-XXX`
- **Domain:** `SYNTHETIC_SIMULATED` | `REAL_OFFLINE_VIDEO`
- **Collection Date Range:** YYYY-MM-DD to YYYY-MM-DD
- **License / Data Rights:** [Specify License or University/Agency Research Agreement]
- **Cryptographic Hash (SHA256):** `[sha256 hash]`

---

## 2. Dataset Composition
- **Total Duration / Frames:** [e.g. 120 minutes / 180,000 frames]
- **Annotated Objects:** [e.g. 45,000 bounding boxes]
- **Classes Breakdown:**
  - `motorcycle`: XX%
  - `passenger_car`: XX%
  - `bus`: XX%
  - `truck`: XX%
  - `ambulance`: XX%

---

## 3. Privacy & Scrubbing Protocol
- [ ] Automated Gaussian blur applied to human faces.
- [ ] Automated plate blurring applied to all identifiable vehicles.
- [ ] No personal identity or geospatial location tags identifying private residences.

---

## 4. Train / Validation / Test Splitting
- **Split Strategy:** Scene-based split (Partitioned by intersection location and recording session).
- **Leakage Prevention:** Adjacent frames within the same 5-minute video window are strictly kept within the same partition.
- **Split Ratios:** Train: 70%, Validation: 15%, Test: 15%.

