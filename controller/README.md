# ClearWayAI Coordination & Safety Controller (`controller`)

Contains the core moving-horizon multi-intersection corridor coordinator and the mathematically verified **Signal Safety Gateway**.

---

## 1. Directory Structure

```
controller/
├── mission/                # Emergency Mission lifecycle manager & Multi-Node ETA estimator (Task 37)
├── safety/                 # Deterministic Signal Safety Gateway & Conflict Matrices
├── scheduler/              # Moving-horizon multi-node pre-clearance scheduler (Task 38)
├── recovery/               # Post-transit smooth recovery state machine (Task 40)
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

## 3. Just-In-Time Pre-Clearance Algorithm (Task 38 VERIFIED)

Managed via `controller/scheduler/`:
- **Pre-Clearance Trigger Formulation:**
  $$\Delta t_{\text{trigger}} = \text{ETA}_{\text{EV}} - \hat{T}_{\text{clear}} - T_{\text{transition}} - T_{\text{buffer}}$$
  - $\text{ETA}_{\text{EV}}$: Kinematic arrival time evaluated by `MultiNodeETAEvaluator`.
  - $\hat{T}_{\text{clear}}$: Queue discharge shockwave duration predicted by `UnifiedClearancePredictor` (Champion models: Gradient Boosting / GRU).
  - $T_{\text{transition}}$: Deterministic safety clearance interval ($T_{\text{yellow}} + T_{\text{all\_red}}$) respecting cross-street minimum green ($10.0\text{s}$).
  - $T_{\text{buffer}}$: Configurable safety margin ($2.0\text{s}$) absorbing arrival noise.

- **Deterministic Pre-Clearance State Machine:**
  ```mermaid
  stateDiagram-v2
      [*] --> MONITORING: Mission Inactive
      MONITORING --> ARMED: Mission Dispatched
      ARMED --> TRANSITIONING: Delta_trigger <= 0
      TRANSITIONING --> HOLDING_GREEN: Yellow & All-Red Complete
      HOLDING_GREEN --> EV_PASSING: Dist <= 50m
      EV_PASSING --> CLEARED: Dist > Stopline + 15m
      CLEARED --> RECOVERING: Hand-off to Recovery
      RECOVERING --> MONITORING: Nominal Plan Restored
      HOLDING_GREEN --> MONITORING: Watchdog Timeout (>60s)
  ```

- **JIT Advantage vs. Baselines:**
  - **B1 (Reactive Local Opticom, 100m):** Triggers too late when queues exceed 50m, forcing emergency vehicles to brake behind discharging queues.
  - **B2 (Corridor Coordination Green-Wave):** Locks all corridor intersections prematurely when vehicle enters at $x = -200\text{m}$, creating massive cross-street congestion.
  - **ClearWayAI JIT:** Actuates each intersection *dynamically* based on its queue length $\hat{T}_{\text{clear}}$, achieving zero emergency stop delay while minimizing side-street disruption.
- **Fail-Safe & Anti-Starvation Guards:**
  - Maximum green hold watchdog ($60.0\text{s}$) aborts preemption if the emergency vehicle breaks down or stalls.
  - Automatic fallback to Tier 1 Kinematic Shockwave or Tier 2 Safe Default ($25.0\text{s}$) if AI perception or state confidence degrades.
- **Latency SLA:** Corridor-wide multi-intersection evaluation executes in $< 1.5\text{ ms}$.

---

## 4. Signal Safety Gateway Invariants

The Safety Gateway intercepts all proposed phase plans:
1. **Green Conflict Matrix:** Prevents conflicting traffic movements from showing Green at the same time.
2. **Minimum Green Time:** Protects driver safety by enforcing a minimum green duration ($T_{\text{min\_green}} \ge 10\text{s}$).
3. **Mandatory Yellow & All-Red:** Enforces yellow (3–4s) and all-red clearance intervals (2s).
4. **Pedestrian Protection:** Guarantees minimum walk and pedestrian clearance timers.
5. **Fail-Safe Watchdog:** Reverts automatically to fixed-time fallback if heartbeats expire (>2s).
