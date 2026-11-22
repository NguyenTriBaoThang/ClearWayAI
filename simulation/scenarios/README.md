# ClearWayAI Traffic Demand Scenarios (`simulation/scenarios`)

> **Synthetic Mixed Traffic Generation, Congestion Load Profiles, and Emergency Missions (ADR-0005 & ADR-0006)**

---

## 1. Overview

This module generates deterministic, realistic traffic demand for the Oak–5th Avenue 4-node arterial corridor. Traffic reflects authentic **Vietnamese urban mobility dynamics**, where motorcycles account for 70–85% of traffic volume and execute lateral sublane filtering between queued passenger cars.

---

## 2. Vietnamese Mixed Vehicle Fleet & Emergency Vehicles

| Vehicle Class | Mix % | Length ($m$) | Width ($m$) | Sublane Model | Lateral Alignment | Max Speed ($km/h$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Motorcycle** | **75%** | $1.90$ | $0.70$ | `SL2015` | `arbitrary` | $50$ ($13.89\text{ m/s}$) |
| **Passenger Car** | **15%** | $4.60$ | $1.90$ | `SL2015` | `center` | $60$ ($16.67\text{ m/s}$) |
| **SUV / Crossover** | **5%** | $4.90$ | $2.00$ | `SL2015` | `center` | $60$ ($16.67\text{ m/s}$) |
| **Transit Bus** | **3%** | $11.00$ | $2.50$ | `SL2015` | `center` | $50$ ($13.89\text{ m/s}$) |
| **Delivery Truck** | **2%** | $8.50$ | $2.50$ | `SL2015` | `center` | $45$ ($12.50\text{ m/s}$) |
| **AMB-339 (Ambulance)** | Mission-Injected | $6.50$ | $2.20$ | `SL2015` | `arbitrary` | $80$ ($22.22\text{ m/s}$) |
| **Fire Engine** | Mission-Injected | $9.00$ | $2.50$ | `SL2015` | `center` | $70$ ($19.44\text{ m/s}$) |

---

## 3. Standard Loading Scenarios

| Scenario ID | Nominal Flow Rate | Queue Dynamics | Purpose |
| :--- | :---: | :--- | :--- |
| **`free_flow`** | $\approx 1,800\text{ veh/h}$ | Free flow, green-wave passage, zero queue delay | Baseline free travel time measurement |
| **`normal`** | $\approx 3,600\text{ veh/h}$ | Standard signal cycle queues ($5\text{--}15\text{ veh}$) | Nominal adaptive signal optimization |
| **`peak`** | $\approx 6,200\text{ veh/h}$ | Heavy congestion, long queues ($30\text{--}60\text{ veh}$) | Emergency corridor pre-clearance evaluation |
| **`spillback`** | $\approx 8,500\text{ veh/h}$ | Gridlock & inter-junction queue spillback (B $\to$ C $\to$ D) | Stress-testing moving-horizon pre-clearance |

---

## 4. Emergency Mission Injection & Blue-Light Scenarios

```bash
# Inject AMB-339 into peak scenario at t=60s
python simulation/scenarios/emergency_mission.py --scenario peak --depart 60.0

# Generate all 3 emergency presets (normal, peak, spillback)
python simulation/scenarios/emergency_mission.py --all
```

Pre-configured emergency presets:
- `corridor_normal_emergency.sumocfg`: AMB-339 departs at $t=45\text{ s}$
- `corridor_peak_emergency.sumocfg`: AMB-339 departs at $t=60\text{ s}$
- `corridor_spillback_emergency.sumocfg`: AMB-339 departs at $t=75\text{ s}$

See [EMERGENCY_CORRIDOR_SPEC.md](EMERGENCY_CORRIDOR_SPEC.md) for full blue-light yielding equations and lateral corridor clearance analysis.
