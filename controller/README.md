# ClearWayAI Coordination & Safety Controller (`controller`)

Contains the core moving-horizon multi-intersection corridor coordinator and the mathematically verified **Signal Safety Gateway**.

---

## 1. Directory Structure

```
controller/
├── mission/                # Emergency Mission lifecycle manager & Multi-Node ETA estimator (Task 37)
├── safety/                 # Deterministic Signal Safety Gateway & Conflict Matrices (Task 41)
├── scheduler/              # Moving-horizon multi-node pre-clearance scheduler & corridor coordinator (Tasks 38 & 39)
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

Managed via `controller/scheduler/preclearance_controller.py`:
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

- **Fail-Safe & Anti-Starvation Guards:**
  - Maximum green hold watchdog ($60.0\text{s}$) aborts preemption if the emergency vehicle breaks down or stalls.
  - Automatic fallback to Tier 1 Kinematic Shockwave or Tier 2 Safe Default ($25.0\text{s}$) if AI perception or state confidence degrades.

---

## 4. Moving-Horizon Corridor Coordinator (Task 39 VERIFIED)

Managed via `controller/scheduler/corridor_coordinator.py`:
- **Moving-Horizon Coordination Window:**
  - Spatial lookahead horizon ($H_{\text{dist}} = 750.0\text{m}$) and temporal horizon ($H_{\text{time}} = 45.0\text{s}$).
  - Nodes outside the moving horizon remain in nominal Webster fixed-time or adaptive signal cycles, avoiding premature network-wide cross-street gridlock.
- **Cascading Green Wave Offset Synchronization:**
  - Dynamic inter-node offset:
    $$\Delta t_{\text{offset}}(k, k+1) = \text{ETA}(k+1) - \text{ETA}(k) \approx \frac{300\text{ m}}{18.5\text{ m/s}} \approx 16.2\text{ s}$$
  - Green wave band cascades smoothly along Nodes A $\to$ B $\to$ C $\to$ D, opening green just-in-time as the vehicle progresses.
- **Queue Spillback Detection & Pre-emptive Flushing:**
  - Monitors link storage occupancy ($L_{\text{queue}} > 0.5 \times \text{LinkLength}$, e.g. $> 150\text{m}$ on a 300m link).
  - Pre-emptively advances downstream node trigger time by $\Delta t_{\text{advance}} = \min(12.0\text{s}, \frac{L_{\text{queue}} - 150}{v_{\text{discharge}}})$ to flush downstream queues before the upstream platoon arrives.
- **Immediate Tail Recovery Handoff:**
  - As soon as the emergency vehicle clears an intersection stopline by $15\text{m}$, that node is immediately freed from green hold and marked as `CLEARED`, handing off to the recovery controller.
- **Corridor Lifecycle State Machine:**
  `STANDBY` $\to$ `CORRIDOR_ARMED` $\to$ `ACTIVE_GREEN_WAVE` $\to$ `TRANSIT_IN_PROGRESS` $\to$ `ALL_CLEARED`.

---

## 5. Post-Clearance Smooth Recovery State Machine (Task 40 VERIFIED)

Managed via `controller/recovery/recovery_controller.py`:
- **Green Debt Formulation:**
  $$G_{\text{debt}} = \min\left(36.0\text{s}, T_{\text{preempt}} \times \frac{G_{\text{cross}}}{C} + \frac{L_{\text{queue}}}{v_{\text{sat}}}\right)$$
  - Quantifies unserved cross-street vehicle demand accumulated during priority preemption hold.
- **Multi-Cycle Amortization (Anti-Shock Recovery):**
  - Spreads green debt repayment over $N_{\text{cycles}} = 3$ cycles:
    $$\Delta g_{\text{bonus}}^{(c)} = \min\left(12.0\text{s}, \frac{G_{\text{debt\_remaining}}}{N_{\text{cycles}} - c + 1}\right)$$
  - Enforces safety split bounds: Arterial green floor $G_{\text{art\_min}} \ge 15.0\text{s}$, Cross green cap $G_{\text{cross\_max}} \le 45.0\text{s}$.
- **Master Clock Offset Resynchronization:**
  - Re-aligns local cycle offset with corridor master clock ($\delta\phi \le 1.5\text{s}$) to smoothly restore multi-intersection green waves.
- **Deterministic State Machine:**
  `INACTIVE` $\to$ `HANDOFF` $\to$ `COMPENSATING` $\to$ `RESYNCHRONIZING` $\to$ `EQUILIBRIUM_RESTORED`.
- **Fail-Safe Watchdog:** Maximum recovery ceiling $180.0\text{s}$ forces equilibrium if unexpected disruptions occur.

---

## 6. Independent Signal Safety Gateway (Task 41 VERIFIED)

Managed via `controller/safety/signal_safety_gateway.py`:
Emulates a zero-trust hardware **Malfunction Management Unit (MMU)** / **Conflict Monitor Unit (CMU)** intercepting all proposed phase commands before execution:
1. **INV-01 (Conflict-Free Vehicular Mutual Exclusion):**
   - Intercepts and blocks conflicting green-green and green-yellow commands; trips immediately to `FAILSAFE_ALL_RED`.
2. **INV-02 (Minimum Green Interval Enforcement):**
   - Enforces $T_{\text{min\_green}} \ge 10.0\text{s}$. Clamps early truncation attempts safely to Green.
3. **INV-03 (Maximum Green Ceiling Enforcement):**
   - Enforces $T_{\text{max\_green}} \le 75.0\text{s}$. Forces transition to Yellow to prevent cross-street starvation.
4. **INV-04 (Mandatory Yellow Change Interval):**
   - Enforces ITE kinematic stopping interval ($T_{\text{yellow}} \ge 3.0\text{s}$). Prohibits skipping or truncating Yellow.
5. **INV-05 (Mandatory All-Red Clearance Interval):**
   - Enforces intersection box clearance interval ($T_{\text{all\_red}} \ge 2.0\text{s}$) before granting conflicting green.
6. **INV-06 (Heartbeat Watchdog & Communication Loss Fallback):**
   - If telemetry or heartbeat signal is lost for $> 2.0\text{s}$, autonomously reverts to `FALLBACK_WEBSTER` localized fixed-time coordination.
- **Latency SLA:** Hardware-level sub-millisecond evaluation ($< 0.1\text{ ms}$).
