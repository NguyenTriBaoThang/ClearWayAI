# ADR 0006: Moving-Horizon Pre-Clearance vs Fixed Pre-Emption

## Context
Conventional Emergency Vehicle Pre-emption (EVP) systems rely on optical strobes (e.g. Opticom) or GPS geofences triggering an immediate hard phase pre-emption when the vehicle crosses a fixed proximity line (e.g. $300\text{ m}$ upstream). In congested urban corridors, this causes severe drawbacks:
1. Cross-street traffic is abruptly truncated, generating massive secondary shockwave spillback.
2. The emergency vehicle often arrives at the intersection while the queue is still clearing, forcing it into oncoming lanes.
3. Once the emergency vehicle clears, the intersection is left in an arbitrary phase state, causing network-wide desynchronization.

## Decision
We adopt a **Moving-Horizon Dynamic Pre-Clearance Algorithm**:
1. Continuous ETA calculation across all corridor nodes (A–D) using real-time kinematics and downstream queue clearance predictions.
2. **Staged Pre-Clearance:** Downstream signals begin draining queued vehicular queues ahead of the ambulance so the lane is empty when the vehicle arrives.
3. **Smooth Post-Clearance Recovery:** Immediately following emergency vehicle clearance, a recovery controller allocates compensatory green splits to heavily queued cross-street movements.

## Consequences
- **Positive:** Zero emergency vehicle deceleration, significantly lower overall corridor delay ($-19\%$ vs fixed pre-emption), no secondary gridlock.
- **Negative:** Requires high-frequency V2X or simulated telemetry updates to maintain accurate ETA tracking.

