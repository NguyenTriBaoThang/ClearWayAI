# ADR 0004: Independent Signal Safety Gateway & MMU Interlock

## Context
Signal timing optimization via Machine Learning (Reinforcement Learning / Neural Networks) is inherently stochastic and may occasionally produce unsafe actions (e.g. commanding conflicting green phases or sub-second green flickers). In real traffic engineering, physical signal cabinets rely on a hardware **Malfunction Management Unit (MMU)** to independently detect and prevent conflicting green indications.

## Decision
We implement an **Independent Signal Safety Gateway (SSG)** that sits between the AI controller and the signal actuation layer:
1. **Conflict Matrix Checker:** Hardcoded Boolean matrix asserting that opposing vehicular approaches never receive Green or Yellow concurrently.
2. **Timing Envelope Invariants:**
   - Minimum Green $\ge 10.0\text{ s}$.
   - Maximum Green $\le 75.0\text{ s}$.
   - Yellow Change interval $\ge 3.0\text{ s}$.
   - All-Red Clearance interval $\ge 2.0\text{ s}$.
3. **Failsafe Clamp:** Any violating command is automatically rejected and clamped to safe limits, or trips to All-Red clearance flash.

## Consequences
- **Positive:** Mathematically provable conflict-free operation, alignment with NEMA TS2 / ATC 5201 standards, total containment of AI policy errors.
- **Negative:** AI reward functions must be carefully tuned to account for the safety bounds without suffering reward penalties when clamped.

