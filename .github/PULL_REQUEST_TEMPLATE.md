## Description
<!-- Provide a concise description of what this PR introduces, fixes, or enhances. -->

**Related Task(s):** Txx (refer to [TASK_BOARD.md](../docs/TASK_BOARD.md))  
**Type of Change:**
- [ ] `feat`: New feature or capability
- [ ] `fix`: Bug fix
- [ ] `3d`: Three.js / WebGL scene adjustment
- [ ] `sim`: SUMO network, scenario, or TraCI adapter change
- [ ] `ai`: Computer vision or clearance prediction model update
- [ ] `safety`: Controller constraints, safety gateway, or fail-safe logic
- [ ] `docs`: Documentation, README, or experiment notes
- [ ] `chore`: Maintenance, dependencies, or CI/CD

---

## Safety & Operational Boundary Verification
> [!IMPORTANT]
> ClearWayAI enforces strict simulation and safety ranh giới. Please verify:
- [ ] **SIMULATION_ONLY:** All traffic signal adjustments are confined to SUMO simulation or isolated physical test bench.
- [ ] **No Public Overrides:** No commands bypass yellow/all-red transition rules or green-conflict matrices.
- [ ] **Data Provenance Labeled:** All telemetry is explicitly tagged (`DEMO_FIXTURE`, `SUMO_SIMULATED`, `OFFLINE_VIDEO`, `SHADOW_ADVISORY`, or `LIVE_CONNECTED`). No mock data is claimed as real field telemetry.
- [ ] **Privacy & Security:** No raw sensitive camera footage, unblurred faces/license plates, or credentials committed.

---

## Quality Checklist
- [ ] **Automated Tests:** `python -m pytest` passes locally.
- [ ] **Typecheck & Build:** `pnpm build` succeeds across `packages/shared`, `apps/web`, and `docs-site`.
- [ ] **3D Rendering Quality:** WebGL scene maintains >= 30 FPS with no clipping or floating meshes.
- [ ] **Documentation:** `docs/PROJECT_STATUS.md` and module READMEs updated accordingly.
- [ ] **Visual Proof / Screenshots:** Attached below for any UI, 3D viewport, or simulation output changes.

---

## Visual Evidence / Screenshots / Simulation Logs
<!-- Attach screenshots, gif/mp4 screen recordings, or terminal test logs here -->

```bash
# Paste verification test output or reproduction command here
```
