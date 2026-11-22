# ADR 0002: Strict Data Provenance & Simulation-Only Safety Mode

## Context
Intelligent transportation systems often suffer from ambiguous claims where synthetic, mock, or replay data is misrepresented as live physical street deployment. Furthermore, deploying autonomous signal override logic to real-world street intersections carries catastrophic collision hazards.

## Decision
We enforce strict **Data Provenance Gating** and a default **Simulation-Only Mode** across the entire stack:
1. Every data contract carries an explicit `data_provenance` tag (`DEMO_FIXTURE`, `SUMO_SIMULATED`, `OFFLINE_VIDEO`, `SHADOW_ADVISORY`, `LIVE_CONNECTED`).
2. The system defaults to `SIMULATION` mode with `simulation_only = true` and `public_signal_control_permitted = false`.
3. In all user interfaces, components display unambiguous status badges (e.g. `Simulated V2X Network`, `DEMO_FIXTURE`).
4. Fake static raster screenshots of traffic are strictly forbidden in production code.

## Consequences
- **Positive:** Uncompromising scientific and engineering honesty, zero hazard to public roads, explicit testability without hardware dependencies.
- **Negative:** Requires continuous maintenance of realistic synthetic fixtures and mock streams for full dashboard demonstration.

