# ClearWayAI Physical Demonstration Bench: Bill of Materials (BOM)

This document lists all hardware components, specifications, reference suppliers, and cost estimates required to assemble the physical 4-intersection traffic demonstration testbench.

---

## 1. Component List & Cost Breakdown

| Item | Component Description | Specs / Model | Qty | Unit Price (VND) | Unit Price (USD) | Total (VND) | Total (USD) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | **ESP32 DevKit V1 Board** | 30-pin / 38-pin, Dual Core 240MHz, USB-CP2102/CH340 | 1 | 95,000 ₫ | $3.80 | 95,000 ₫ | $3.80 |
| **2** | **Mini Traffic Light LED Modules** | 3-LED Module (Red, Yellow, Green, common cathode, 5V/3.3V) | 8 | 12,000 ₫ | $0.48 | 96,000 ₫ | $3.84 |
| **3** | **74HC595 Shift Registers** | 8-bit Serial-In Parallel-Out Shift Register DIP-16 | 3 | 5,000 ₫ | $0.20 | 15,000 ₫ | $0.60 |
| **4** | **Breadboard (Solderless)** | MB-102 830 tie-points transparent / white | 2 | 25,000 ₫ | $1.00 | 50,000 ₫ | $2.00 |
| **5** | **DuPont Jumper Wires** | 40-pin Male-to-Male & Male-to-Female, 20cm | 1 set | 20,000 ₫ | $0.80 | 20,000 ₫ | $0.80 |
| **6** | **Current Limiting Resistors** | 220 Ω ±5% 1/4W Metal Film Resistors | 24 | 200 ₫ | $0.01 | 4,800 ₫ | $0.24 |
| **7** | **Decoupling Capacitors** | 100 nF (0.1 µF) Ceramic Capacitor 50V | 3 | 500 ₫ | $0.02 | 1,500 ₫ | $0.06 |
| **8** | **Emergency Strobe LED / Buzzer** | High-intensity 5mm Blue/Amber LED + 5V Active Buzzer | 1 | 8,000 ₫ | $0.32 | 8,000 ₫ | $0.32 |
| **9** | **USB Cable** | USB-A to Micro-USB / Type-C Data Cable (1.0m) | 1 | 18,000 ₫ | $0.72 | 18,000 ₫ | $0.72 |
| **10** | **Foam Board / Acrylic Base** | 50cm x 20cm baseplate for road layout | 1 | 35,000 ₫ | $1.40 | 35,000 ₫ | $1.40 |
| **TOTAL** | **Complete Physical Testbench** | **All 10 items** | **—** | **343,300 ₫** | **~$13.78** | **343,300 ₫** | **~$13.78** |

---

## 2. Supplier Sourcing & Availability

- **Vietnam:**
  - Linh Kiện Điện Tử Cầu Giấy / Nshop / BanLinhKien / Shopee VN (Delivery in 1–2 days).
  - All parts are standard educational electronics modules and continuously in stock.
- **International:**
  - AliExpress, DigiKey, Mouser, Amazon.

---

## 3. Tooling Requirements
- **No soldering required** if using standard solderless breadboard MB-102 and pre-soldered LED traffic modules with pin headers.
- Wire strippers (optional if trimming jumper cables).
- Multimeter for checking 5V/3.3V rail voltage and ground continuity.

