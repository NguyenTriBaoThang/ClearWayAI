# ClearWayAI Scientific Experiments & Benchmark Protocol

This document governs the empirical benchmarking, multi-seed evaluation, and ablation protocols designed to scientifically validate ClearWayAI.

---

## 1. Experimental Baselines

To ensure fair and rigorous comparison, all models are evaluated on identical network configurations and random seeds:

| Baseline ID | Description | Signal Control Strategy |
| :--- | :--- | :--- |
| **B0** | Fixed-Time Control | Pre-programmed Webster fixed cycle without priority preemption. |
| **B1** | Reactive Local Preemption | Detects emergency vehicle at 50m distance and forces immediate green. |
| **B2** | Distance/ETA Corridor | Static distance-based green wave along the planned route. |
| **B3** | ClearWay AI (Proposed) | Moving-horizon predictive pre-clearance with AI clearance time estimation. |

---

## 2. Evaluation Metrics

1. **Emergency Vehicle Travel Time ($T_{\text{EV}}$):** Total transit time through corridor Node A to Node D (seconds).
2. **Emergency Vehicle Stop Count ($N_{\text{stops}}$):** Frequency of emergency vehicle deceleration below $5\text{ km/h}$.
3. **Network Secondary Delay ($\bar{D}_{\text{network}}$):** Average delay per vehicle for non-priority approaches (seconds/veh).
4. **Corridor Recovery Time ($T_{\text{rec}}$):** Duration until normal cycle split equilibrium is restored after ambulance exit.

---

## 3. Multi-Seed Replication Protocol

All experiments are conducted across at least **10 independent random seeds** per traffic severity level:
- Demand Scenarios: `Free` ($400\text{ veh/h/lane}$), `Normal` ($800\text{ veh/h/lane}$), `Peak` ($1200\text{ veh/h/lane}$), `Spillback` ($1600\text{ veh/h/lane}$).
- Random Seeds: `[42, 101, 2024, 777, 999, 1337, 8888, 54321, 12345, 98765]`.
- Report: Mean $\pm$ 95% Confidence Interval (Student's t-distribution).
