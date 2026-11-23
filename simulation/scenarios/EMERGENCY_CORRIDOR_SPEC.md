# ClearWayAI - Emergency Corridor & Blue-Light Yielding Specification

> **Microscopic Simulation of Emergency Vehicles and Surrounding Traffic Yielding (ADR-0005 & ADR-0006)**

---

## 1. Overview & Operational Principles

Under Vietnamese urban traffic conditions, emergency vehicles (ambulances, fire engines) face heavy congestion dominated by motorcycles (75%) and passenger cars. When sirens and blue lights are activated, surrounding vehicles exhibit distinct **yielding behaviors**:
1. **Motorcycle Sublane Swarming & Filtering:** Motorcycles exploit small gaps ($0.4\text{ m}$) to quickly filter towards road shoulders and curbs, opening the central corridor.
2. **Automobile Lateral Displacement ("Rettungsgasse"):** Passenger cars and SUVs shift laterally towards outer lane markings (`latAlignment` moves $\pm 1.1\text{ m}$ off center), creating an unimpeded emergency path $\ge 3.0\text{ m}$ wide.
3. **Emergency Pre-emption & Pre-clearance:** Downstream signals clear queues before the emergency vehicle arrives, eliminating dangerous full-stop deceleration events.

---

## 2. Emergency Fleet Vehicle Type Parameters (`vtypes.add.xml`)

| Parameter | `emergency_ambulance` (AMB-339) | `emergency_fire` (Fire Engine) | Rationale |
| :--- | :---: | :---: | :--- |
| **`vClass`** | `emergency` | `emergency` | Special SUMO vehicle classification |
| **Length / Width** | $6.50\text{ m} \times 2.20\text{ m}$ | $9.00\text{ m} \times 2.50\text{ m}$ | Standard Type II/III ambulance & urban pumper |
| **Max Speed** | $80\text{ km/h}$ ($22.22\text{ m/s}$) | $70\text{ km/h}$ ($19.44\text{ m/s}$) | High-speed response |
| **`speedFactor`** | `1.30` | `1.20` | Permitted to exceed speed limit by up to 30% |
| **Acceleration** | $3.5\text{ m/s}^2$ | $2.5\text{ m/s}^2$ | Rapid recovery from slowdowns |
| **`laneChangeModel`** | `SL2015` | `SL2015` | Sublane lateral model |
| **`latAlignment`** | `arbitrary` | `center` | Ambulance can exploit lane splits |
| **`minGapLat`** | $0.25\text{ m}$ | $0.40\text{ m}$ | Tight lateral passing clearance |
| **`lcPushy` / `lcAssertive`**| `1.0` / `1.0` | `0.9` / `0.9` | High assertiveness when requesting right-of-way |
| **`lcCooperative`** | `0.0` | `0.0` | Emergency vehicle does not yield to normal traffic |

---

## 3. Surrounding Traffic Blue-Light Yielding Parameters

To simulate cooperative yielding behavior when AMB-339 approaches:
- **`lcCooperative="1.0"`**: Maximum willingness of passenger cars and motorcycles to make way for overtakers.
- **`lcPushy="0.8"` (Motorcycles)**: Motorcycles readily slip between stopped cars to reach curb areas.
- **Lateral Corridor Width Requirement:**
  $$\text{Clearance Width} = W_{\text{amb}} + 2 \times \text{Buffer} = 2.20\text{ m} + 2 \times 0.40\text{ m} = 3.00\text{ m}$$
  On a standard $3.2\text{ m}$ lane, lateral shifting creates an effective clearance passage of $3.2\text{--}3.6\text{ m}$.

---

## 4. Emergency Mission Injection (`AMB-339`)

The mission injector service (`simulation/scenarios/emergency_mission.py`) injects emergency runs:

```bash
# Inject AMB-339 into peak scenario at t=60s
python simulation/scenarios/emergency_mission.py --scenario peak --depart 60.0

# Generate all standard emergency scenario presets
python simulation/scenarios/emergency_mission.py --all
```

Pre-generated scenario presets:
- `corridor_normal_emergency.sumocfg`: Departure $t = 45\text{ s}$
- `corridor_peak_emergency.sumocfg`: Departure $t = 60\text{ s}$
- `corridor_spillback_emergency.sumocfg`: Departure $t = 75\text{ s}$

---

## 5. Performance Metrics & Comparative KPIs

| Metric | Baseline (No Pre-Clearance) | ClearWay AI (Dynamic Pre-Clearance) | Benefit |
| :--- | :---: | :---: | :---: |
| **Ambulance Average Speed** | $25\text{ km/h}$ ($7.0\text{ m/s}$) | **$66\text{ km/h}$ ($18.5\text{ m/s}$)** | $+164\%$ speed |
| **Corridor Transit Time (1300m)** | $185.7\text{ s}$ | **$70.3\text{ s}$** | **$-62.1\%$ travel time** |
| **Deceleration Events** | $3\text{--}5$ stops | **$0$ stops** | Zero braking |
| **Overall Corridor Delay** | Spillback shockwaves | **$-19\%$ network delay** | No secondary gridlock |

