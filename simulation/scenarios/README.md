# ClearWayAI Traffic Demand Scenarios (`simulation/scenarios`)

> **Synthetic Mixed Traffic Generation & Congestion Load Profiles (ADR-0005)**

---

## 1. Overview

This module generates deterministic, realistic traffic demand for the Oak–5th Avenue 4-node arterial corridor. Traffic reflects authentic **Vietnamese urban mobility dynamics**, where motorcycles account for 70–85% of traffic volume and execute lateral sublane filtering between queued passenger cars.

---

## 2. Vietnamese Mixed Vehicle Fleet

| Vehicle Class | Mix % | Length ($m$) | Width ($m$) | Sublane Model | Lateral Alignment | Max Speed ($km/h$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Motorcycle** | **75%** | $1.90$ | $0.70$ | `SL2015` | `arbitrary` | $50$ ($13.89\text{ m/s}$) |
| **Passenger Car** | **15%** | $4.60$ | $1.90$ | `SL2015` | `center` | $60$ ($16.67\text{ m/s}$) |
| **SUV / Crossover** | **5%** | $4.90$ | $2.00$ | `SL2015` | `center` | $60$ ($16.67\text{ m/s}$) |
| **Transit Bus** | **3%** | $11.00$ | $2.50$ | `SL2015` | `center` | $50$ ($13.89\text{ m/s}$) |
| **Delivery Truck** | **2%** | $8.50$ | $2.50$ | `SL2015` | `center` | $45$ ($12.50\text{ m/s}$) |

---

## 3. Standard Loading Scenarios

| Scenario ID | Nominal Flow Rate | Queue Dynamics | Purpose |
| :--- | :---: | :--- | :--- |
| **`free_flow`** | $\approx 1,800\text{ veh/h}$ | Free flow, green-wave passage, zero queue delay | Baseline free travel time measurement |
| **`normal`** | $\approx 3,600\text{ veh/h}$ | Standard signal cycle queues ($5\text{--}15\text{ veh}$) | Nominal adaptive signal optimization |
| **`peak`** | $\approx 6,200\text{ veh/h}$ | Heavy congestion, long queues ($30\text{--}60\text{ veh}$) | Emergency corridor pre-clearance evaluation |
| **`spillback`** | $\approx 8,500\text{ veh/h}$ | Gridlock & inter-junction queue spillback (B $\to$ C $\to$ D) | Stress-testing moving-horizon pre-clearance |

---

## 4. Usage & Generation Commands

### Generate Preset Scenarios (5-minute simulation runs)
```bash
# Generate all 4 standard scenario route presets (Seed: 42)
python simulation/scenarios/generate_demand.py --all

# Generate specific scenario with custom duration and seed
python simulation/scenarios/generate_demand.py --scenario peak --duration 1800 --seed 123 --output simulation/scenarios/corridor_peak_30min.rou.xml
```

### Running Simulations via SUMO CLI
```bash
# Run peak congestion simulation in SUMO GUI
sumo-gui -c simulation/scenarios/corridor_peak.sumocfg

# Run headless command-line simulation
sumo -c simulation/scenarios/corridor_normal.sumocfg
```
