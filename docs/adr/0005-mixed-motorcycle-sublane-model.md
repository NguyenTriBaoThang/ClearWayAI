# ADR 0005: SUMO Sublane Model for Vietnamese Mixed Traffic

## Context
Standard macroscopic and microscopic traffic models assume strict lane-following discipline where vehicles occupy a single lane centered between striping markings. In Vietnamese urban traffic (e.g. Ho Chi Minh City, Hanoi), motorcycles comprise 70–85% of traffic volume. Motorcycles perform lateral filtering, swarming, side-by-side riding within a single lane, and stopline creep ahead of passenger cars during red signals.

## Decision
We configure Eclipse SUMO with the **Sublane Model** (`laneChangeModel="SL2015"`):
1. Discrete lanes are subdivided into multiple lateral sublanes (width $0.5\text{ m}$ to $0.8\text{ m}$).
2. Vehicles have realistic physical dimensions:
   - Motorcycles: width $0.7\text{ m}$, length $1.9\text{ m}$, minGap $0.4\text{ m}$, lateral alignment `arbitrary`.
   - Passenger Cars: width $1.9\text{ m}$, length $4.6\text{ m}$.
   - Buses: width $2.5\text{ m}$, length $11.0\text{ m}$.
3. Motorcycles can utilize available lateral gaps to filter past stopped passenger cars at signal stoplines.

## Consequences
- **Positive:** Accurate reproduction of real-world Vietnamese saturation flow rates, capacity surge on green onset, and authentic queue dissipation dynamics.
- **Negative:** Increased computational cost per simulation step compared to standard discrete lane models; requires fine-tuning of lateral resolution.

