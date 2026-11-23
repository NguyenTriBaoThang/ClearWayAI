# ClearWayAI Coordination & Safety Controller (`controller`)

Contains the core moving-horizon multi-intersection corridor coordinator and the mathematically verified **Signal Safety Gateway**.

---

## 1. Directory Structure

```
controller/
├── mission/                # Emergency Mission lifecycle manager & Multi-Node ETA estimator (Task 37)
├── safety/                 # Deterministic Signal Safety Gateway & Conflict Matrices
├── scheduler/              # Moving-horizon multi-node pre-clearance scheduler
├── recovery/               # Post-transit smooth recovery state machine
└── README.md
```

---

## 2. Emergency Mission Lifecycle & Multi-Node ETA (Task 37 VERIFIED)

Managed via `controller/mission/`:
- **State Machine Lifecycle:** `PENDING` $\to$ `DISPATCHED` $\to$ `APPROACHING` $\to$ `CORRIDOR_TRANSIT` $\to$ `ARRIVED` (with `ABORTED` / `COMPLETED` handling).
- **Multi-Node Kinematic ETA:** Calculates exact arrival times to each intersection stopline along the 1300m corridor:
  - Node A: Stopline $x = 0.0\text{ m}$ (Distance from West Entry: $200\text{ m}$)
  - Node B: Stopline $x = 300.0\text{ m}$ (Distance: $500\text{ m}$)
  - Node C: Stopline $x = 600.0\text{ m}$ (Distance: $800\text{ m}$)
  - Node D: Stopline $x = 900.0\text{ m}$ (Distance: $1100\text{ m}$)
  - Metropolitan Hospital: Egress Stopline $x = 1100.0\text{ m}$ (Distance: $1300\text{ m}$)
- **Kinematic Formula:** Non-linear acceleration curve ($a = 3.5\text{ m/s}^2$) up to priority cruise speed ($v = 18.5\text{ m/s} \approx 66.6\text{ km/h}$) with dynamic traffic drag and weather adjustments.
- **Latency SLA:** Sub-millisecond calculation ($< 0.5\text{ ms}$).

---

## 3. Signal Safety Gateway Invariants

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

