# ClearWayAI Demonstration & Walkthrough Runbook

A structured script for performing a live demonstration of ClearWayAI to operators, judges, or research evaluators.

---

## 1. Demo Setup & Environment Verification

```bash
# 1. Verify system environment
python -m pytest tests/test_api_smoke.py

# 2. Start services locally
python -m uvicorn apps.api.src.main:app --reload --port 8000
pnpm --filter clearway-web dev
```

---

## 2. 5-Minute Storyboard Outline

- **00:00 – 00:45 | The Problem:** Present congested urban corridor in Ho Chi Minh City / Hanoi with dense motorcycle queues where ambulances lose critical minutes.
- **00:45 – 01:30 | The Architecture:** Introduce ClearWayAI: true WebGL 3D Digital Twin, microscopic simulation with SUMO sublane model, and AI clearance estimation.
- **01:30 – 02:45 | The Live Operations Dashboard:** 
  - Showcase the Operations Center interface matching the reference blueprint.
  - Inspect the Three.js 3D viewport, rotating the camera to demonstrate true isometric 3D geometry.
  - Review the V2X status, approach timing table, and adaptive signal queue chart.
- **02:45 – 04:00 | Simulated Emergency Corridor Dispatch:**
  - Inject an active emergency mission (`AMB-339`).
  - Demonstrate moving-horizon pre-clearance: the Signal Safety Gateway opens green for the corridor approach just in time.
  - Highlight the chevron flow arrows and ambulance HUD callout.
  - Observe queue-aware recovery returning the network to balanced fixed-time equilibrium.
- **04:00 – 05:00 | Empirical Comparison & Conclusion:**
  - Show synchronized side-by-side comparison: Fixed-Time vs ClearWay AI.
  - Conclude with safety invariants: deterministic fail-safes and strict simulation isolation.
