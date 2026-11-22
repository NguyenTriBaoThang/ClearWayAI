# ClearWayAI Coordination & Safety Controller (`controller`)

Contains the core moving-horizon multi-intersection corridor coordinator and the mathematically verified **Signal Safety Gateway**.

---

## 1. Directory Structure

```
controller/
├── safety/                 # Deterministic Signal Safety Gateway & Conflict Matrices
├── scheduler/              # Moving-horizon multi-node pre-clearance scheduler
├── recovery/               # Post-transit smooth recovery state machine
└── README.md
```

---

## 2. Signal Safety Gateway Invariants

The Safety Gateway intercepts all proposed phase plans:
1. **Green Conflict Matrix:** Prevents conflicting traffic movements from showing Green at the same time.
2. **Minimum Green Time:** Protects driver safety by enforcing a minimum green duration ($T_{\text{min\_green}} \ge 10\text{s}$).
3. **Mandatory Yellow & All-Red:** Enforces yellow (3–4s) and all-red clearance intervals (2s).
4. **Pedestrian Protection:** Guarantees minimum walk and pedestrian clearance timers.
5. **Fail-Safe Watchdog:** Reverts automatically to fixed-time fallback if heartbeats expire (>2s).

---

## 3. Pre-clearance Timing Equation

$$\Delta t_{\text{trigger}} = \text{ETA}_{\text{EV}} - \hat{T}_{\text{clear}} - T_{\text{transition}} - T_{\text{buffer}}$$

The corridor is opened just in time as the vehicle arrives, preventing empty green time and excessive private vehicle queuing.
