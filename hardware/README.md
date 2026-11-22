# ClearWayAI Physical Demonstration Bench (`hardware`)

Contains microcontroller firmware (ESP32), circuit schematics, and bill-of-materials (BOM) for the physical miniature intersection testbench.

---

## 1. Directory Structure

```
hardware/
├── firmware/               # Arduino/ESP32 C++ source code
├── schematics/             # Wiring diagrams, pinouts, and breadboard schematics
├── bom/                    # Bill of Materials and component pricing
└── README.md
```

---

## 2. Architecture & Safety

- **Communication:** ESP32 communicates with the backend simulation server via local USB Serial or local MQTT broker.
- **Fail-Safe Watchdog:** If communication drops for >2.0s, the ESP32 automatically drops into local autonomous fixed-time cycling with standard yellow/all-red intervals.
- **Strict Isolation:** The testbench operates on 5V DC and is completely isolated from any public roadside infrastructure.

