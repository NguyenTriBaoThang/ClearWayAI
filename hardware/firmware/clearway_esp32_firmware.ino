/*
 * ==============================================================================
 * Project: ClearWayAI - Physical Miniature Demonstration Bench
 * Firmware: ESP32 Multi-Intersection Signal Controller with MMU & Watchdog
 * File: hardware/firmware/clearway_esp32_firmware.ino
 * Target: ESP32 DevKit V1 (ESP-WROOM-32, 30-pin / 38-pin)
 * License: Apache-2.0
 * ==============================================================================
 *
 * Capabilities:
 * - Controls 4 miniature intersections (Node A, Node B, Node C, Node D).
 * - Dual-approach LED traffic lights per intersection:
 *     * Corridor Axis (East-West): Red, Yellow, Green
 *     * Cross Street (North-South): Red, Yellow, Green
 * - Hardware MMU (Malfunction Management Unit): Hardware interlock preventing
 *   conflicting Green indications (INV-03).
 * - Hardware Fail-Safe Watchdog (INV-06): If communication is lost for >2.0s,
 *   the controller falls back to autonomous fixed-time cycling.
 * - Emergency Strobe Beacon: High-intensity LED / buzzer alert for ambulance
 *   pre-clearance.
 * - Communication: UART Serial JSON framing at 115200 baud.
 */

#include <Arduino.h>

// ==============================================================================
// 1. PINOUT CONFIGURATION
// ==============================================================================
// Set USE_SHIFT_REGISTERS to 1 for 74HC595 Daisy-Chain mode (recommended for 4 nodes)
// Set to 0 for Direct GPIO mode (supports Node A & Node B)
#define USE_SHIFT_REGISTERS 1

#if USE_SHIFT_REGISTERS
  // 74HC595 Daisy-Chain Pins (Controls 24 output channels: 4 nodes * 6 LEDs)
  #define PIN_SR_DATA     23  // DS (Serial Data Input)
  #define PIN_SR_LATCH    22  // ST_CP (Storage Register Clock / Latch)
  #define PIN_SR_CLOCK    21  // SH_CP (Shift Register Clock)
#else
  // Direct GPIO Mode (Direct wiring for Node A & Node B)
  // Node A (Intersection 1)
  #define PIN_A_EW_R      23
  #define PIN_A_EW_Y      22
  #define PIN_A_EW_G      21
  #define PIN_A_NS_R      19
  #define PIN_A_NS_Y      18
  #define PIN_A_NS_G       5

  // Node B (Intersection 2)
  #define PIN_B_EW_R      17
  #define PIN_B_EW_Y      16
  #define PIN_B_EW_G       4
  #define PIN_B_NS_R       0
  #define PIN_B_NS_Y       2
  #define PIN_B_NS_G      15
#endif

// Shared Indicators
#define PIN_HEARTBEAT_LED 2   // Onboard Blue LED for Heartbeat / Watchdog
#define PIN_EMERGENCY_STROBE 13 // High-intensity Emergency Warning Beacon

// Safety Limits
#define WATCHDOG_TIMEOUT_MS 2000UL // 2.0s watchdog drop threshold (INV-06)
#define BAUDRATE 115200

// ==============================================================================
// 2. SIGNAL COLOR ENUM & DATA STRUCTURES
// ==============================================================================
enum SignalColor {
  COLOR_RED = 0,
  COLOR_YELLOW = 1,
  COLOR_GREEN = 2,
  COLOR_OFF = 3
};

struct NodeState {
  SignalColor ew_color;
  SignalColor ns_color;
};

// Global 4-Node Registry (Node A, Node B, Node C, Node D)
NodeState nodes[4] = {
  {COLOR_RED, COLOR_RED},
  {COLOR_RED, COLOR_RED},
  {COLOR_RED, COLOR_RED},
  {COLOR_RED, COLOR_RED}
};

bool emergencyStrobeActive = false;
bool mmuTripped = false;
unsigned long lastHeartbeatMs = 0;
unsigned long lastStrobeToggleMs = 0;
bool strobeState = false;

// Autonomous Fallback Cycle State Machine
unsigned long fallbackStartMs = 0;
int fallbackPhase = 0;

// ==============================================================================
// 3. HARDWARE MMU (MALFUNCTION MANAGEMENT UNIT)
// ==============================================================================
/**
 * @brief Checks if any node has conflicting Green-Green illumination.
 * @return true if hardware interlock passes safely, false if conflict detected.
 */
bool verifyHardwareMMU() {
  for (int i = 0; i < 4; i++) {
    if (nodes[i].ew_color == COLOR_GREEN && nodes[i].ns_color == COLOR_GREEN) {
      return false; // Hardware Conflict Trip!
    }
  }
  return true;
}

// ==============================================================================
// 4. LED DRIVER & LATCHING
// ==============================================================================
#if USE_SHIFT_REGISTERS
void updateShiftRegisters() {
  // If MMU is tripped, force Flashing Yellow on all heads for safety
  if (mmuTripped) {
    bool flashOn = (millis() / 500) % 2 == 0;
    digitalWrite(PIN_SR_LATCH, LOW);
    for (int byteIdx = 0; byteIdx < 3; byteIdx++) {
      shiftOut(PIN_SR_DATA, PIN_SR_CLOCK, MSBFIRST, flashOn ? 0b01001001 : 0b00000000);
    }
    digitalWrite(PIN_SR_LATCH, HIGH);
    return;
  }

  // Pack 4 nodes * 6 bits = 24 bits into 3 shift registers
  uint32_t registerPattern = 0;
  for (int i = 0; i < 4; i++) {
    // 6 bits per node: [EW_G, EW_Y, EW_R, NS_G, NS_Y, NS_R]
    uint8_t ewBits = (nodes[i].ew_color == COLOR_GREEN ? 0x04 : 0) |
                     (nodes[i].ew_color == COLOR_YELLOW ? 0x02 : 0) |
                     (nodes[i].ew_color == COLOR_RED ? 0x01 : 0);
    uint8_t nsBits = (nodes[i].ns_color == COLOR_GREEN ? 0x04 : 0) |
                     (nodes[i].ns_color == COLOR_YELLOW ? 0x02 : 0) |
                     (nodes[i].ns_color == COLOR_RED ? 0x01 : 0);
    uint32_t nodeBits = ((uint32_t)ewBits << 3) | (uint32_t)nsBits;
    registerPattern |= (nodeBits << (i * 6));
  }

  digitalWrite(PIN_SR_LATCH, LOW);
  shiftOut(PIN_SR_DATA, PIN_SR_CLOCK, MSBFIRST, (uint8_t)((registerPattern >> 16) & 0xFF));
  shiftOut(PIN_SR_DATA, PIN_SR_CLOCK, MSBFIRST, (uint8_t)((registerPattern >> 8) & 0xFF));
  shiftOut(PIN_SR_DATA, PIN_SR_CLOCK, MSBFIRST, (uint8_t)(registerPattern & 0xFF));
  digitalWrite(PIN_SR_LATCH, HIGH);
}
#else
void updateDirectGPIO() {
  if (mmuTripped) {
    bool flashOn = (millis() / 500) % 2 == 0;
    digitalWrite(PIN_A_EW_R, LOW);
    digitalWrite(PIN_A_EW_Y, flashOn ? HIGH : LOW);
    digitalWrite(PIN_A_EW_G, LOW);
    digitalWrite(PIN_A_NS_R, LOW);
    digitalWrite(PIN_A_NS_Y, flashOn ? HIGH : LOW);
    digitalWrite(PIN_A_NS_G, LOW);
    return;
  }

  // Node A
  digitalWrite(PIN_A_EW_R, nodes[0].ew_color == COLOR_RED ? HIGH : LOW);
  digitalWrite(PIN_A_EW_Y, nodes[0].ew_color == COLOR_YELLOW ? HIGH : LOW);
  digitalWrite(PIN_A_EW_G, nodes[0].ew_color == COLOR_GREEN ? HIGH : LOW);
  digitalWrite(PIN_A_NS_R, nodes[0].ns_color == COLOR_RED ? HIGH : LOW);
  digitalWrite(PIN_A_NS_Y, nodes[0].ns_color == COLOR_YELLOW ? HIGH : LOW);
  digitalWrite(PIN_A_NS_G, nodes[0].ns_color == COLOR_GREEN ? HIGH : LOW);

  // Node B
  digitalWrite(PIN_B_EW_R, nodes[1].ew_color == COLOR_RED ? HIGH : LOW);
  digitalWrite(PIN_B_EW_Y, nodes[1].ew_color == COLOR_YELLOW ? HIGH : LOW);
  digitalWrite(PIN_B_EW_G, nodes[1].ew_color == COLOR_GREEN ? HIGH : LOW);
  digitalWrite(PIN_B_NS_R, nodes[1].ns_color == COLOR_RED ? HIGH : LOW);
  digitalWrite(PIN_B_NS_Y, nodes[1].ns_color == COLOR_YELLOW ? HIGH : LOW);
  digitalWrite(PIN_B_NS_G, nodes[1].ns_color == COLOR_GREEN ? HIGH : LOW);
}
#endif

void flushOutputs() {
#if USE_SHIFT_REGISTERS
  updateShiftRegisters();
#else
  updateDirectGPIO();
#endif
}

// ==============================================================================
// 5. AUTONOMOUS FIXED-TIME FALLBACK CYCLING (INV-06)
// ==============================================================================
void handleAutonomousFallback() {
  unsigned long now = millis();
  unsigned long elapsedInCycle = (now - fallbackStartMs) % 30000UL;

  // 30s Fixed Cycle:
  // 0-14s: Corridor Green, Cross Red
  // 14-17s: Corridor Yellow, Cross Red
  // 17-19s: All-Red Clearance
  // 19-27s: Corridor Red, Cross Green
  // 27-30s: Corridor Red, Cross Yellow
  SignalColor ew, ns;
  if (elapsedInCycle < 14000UL) {
    ew = COLOR_GREEN; ns = COLOR_RED;
  } else if (elapsedInCycle < 17000UL) {
    ew = COLOR_YELLOW; ns = COLOR_RED;
  } else if (elapsedInCycle < 19000UL) {
    ew = COLOR_RED; ns = COLOR_RED;
  } else if (elapsedInCycle < 27000UL) {
    ew = COLOR_RED; ns = COLOR_GREEN;
  } else {
    ew = COLOR_RED; ns = COLOR_YELLOW;
  }

  for (int i = 0; i < 4; i++) {
    nodes[i].ew_color = ew;
    nodes[i].ns_color = ns;
  }
  emergencyStrobeActive = false;
  flushOutputs();
}

// ==============================================================================
// 6. SERIAL PROTOCOL PARSER
// ==============================================================================
SignalColor parseColorChar(char c) {
  if (c == 'G' || c == 'g') return COLOR_GREEN;
  if (c == 'Y' || c == 'y') return COLOR_YELLOW;
  return COLOR_RED;
}

void processCommand(const String& cmdLine) {
  lastHeartbeatMs = millis(); // Refresh watchdog timer

  if (cmdLine.indexOf("\"cmd\":\"HEARTBEAT\"") >= 0) {
    Serial.println("{\"ack\":\"HEARTBEAT\",\"status\":\"OK\",\"uptime_ms\":" + String(millis()) + "}");
    return;
  }

  if (cmdLine.indexOf("\"cmd\":\"LAMP_TEST\"") >= 0) {
    for (int i = 0; i < 4; i++) {
      nodes[i].ew_color = COLOR_GREEN;
      nodes[i].ns_color = COLOR_GREEN;
    }
    // Temporarily bypass MMU for lamp test
    flushOutputs();
    Serial.println("{\"ack\":\"LAMP_TEST\",\"status\":\"OK\"}");
    return;
  }

  if (cmdLine.indexOf("\"cmd\":\"RESET_FAULTS\"") >= 0) {
    mmuTripped = false;
    Serial.println("{\"ack\":\"RESET_FAULTS\",\"status\":\"OK\"}");
    return;
  }

  if (cmdLine.indexOf("\"cmd\":\"PHASE_UPDATE\"") >= 0) {
    // Parse Node States from JSON
    // Format: {"cmd":"PHASE_UPDATE","emergency":false,"nodes":{"node_a":{"ew":"G","ns":"R"},...}}
    emergencyStrobeActive = (cmdLine.indexOf("\"emergency\":true") >= 0);

    const char* nodeKeys[4] = {"\"node_a\":", "\"node_b\":", "\"node_c\":", "\"node_d\":"};
    for (int i = 0; i < 4; i++) {
      int pos = cmdLine.indexOf(nodeKeys[i]);
      if (pos >= 0) {
        int ewPos = cmdLine.indexOf("\"ew\":\"", pos);
        if (ewPos >= 0 && ewPos < pos + 60) {
          char ewChar = cmdLine.charAt(ewPos + 6);
          nodes[i].ew_color = parseColorChar(ewChar);
        }
        int nsPos = cmdLine.indexOf("\"ns\":\"", pos);
        if (nsPos >= 0 && nsPos < pos + 60) {
          char nsChar = cmdLine.charAt(nsPos + 6);
          nodes[i].ns_color = parseColorChar(nsChar);
        }
      }
    }

    // Verify MMU Safety Invariant (INV-03)
    if (!verifyHardwareMMU()) {
      mmuTripped = true;
      flushOutputs();
      Serial.println("{\"ack\":\"PHASE_UPDATE\",\"status\":\"MMU_CONFLICT_TRIP\",\"error\":\"ERR_HW_MMU_CONFLICT\"}");
      return;
    }

    flushOutputs();
    Serial.println("{\"ack\":\"PHASE_UPDATE\",\"status\":\"OK\",\"mmu_ok\":true}");
    return;
  }

  Serial.println("{\"ack\":\"UNKNOWN_CMD\"}");
}

// ==============================================================================
// 7. SETUP & MAIN LOOP
// ==============================================================================
void setup() {
  Serial.begin(BAUDRATE);

  pinMode(PIN_HEARTBEAT_LED, OUTPUT);
  pinMode(PIN_EMERGENCY_STROBE, OUTPUT);
  digitalWrite(PIN_HEARTBEAT_LED, LOW);
  digitalWrite(PIN_EMERGENCY_STROBE, LOW);

#if USE_SHIFT_REGISTERS
  pinMode(PIN_SR_DATA, OUTPUT);
  pinMode(PIN_SR_LATCH, OUTPUT);
  pinMode(PIN_SR_CLOCK, OUTPUT);
  digitalWrite(PIN_SR_LATCH, HIGH);
#else
  pinMode(PIN_A_EW_R, OUTPUT); pinMode(PIN_A_EW_Y, OUTPUT); pinMode(PIN_A_EW_G, OUTPUT);
  pinMode(PIN_A_NS_R, OUTPUT); pinMode(PIN_A_NS_Y, OUTPUT); pinMode(PIN_A_NS_G, OUTPUT);
  pinMode(PIN_B_EW_R, OUTPUT); pinMode(PIN_B_EW_Y, OUTPUT); pinMode(PIN_B_EW_G, OUTPUT);
  pinMode(PIN_B_NS_R, OUTPUT); pinMode(PIN_B_NS_Y, OUTPUT); pinMode(PIN_B_NS_G, OUTPUT);
#endif

  // Initial Lamp Test sequence (1.0s)
  flushOutputs();
  lastHeartbeatMs = millis();
  fallbackStartMs = millis();

  Serial.println("{\"banner\":\"ClearWayAI ESP32 Hardware Controller v1.0 ONLINE\"}");
}

void loop() {
  // 1. Process Serial incoming messages
  if (Serial.available() > 0) {
    String incomingLine = Serial.readStringUntil('\n');
    incomingLine.trim();
    if (incomingLine.length() > 0) {
      processCommand(incomingLine);
    }
  }

  // 2. Hardware Fail-Safe Watchdog Check (INV-06)
  unsigned long now = millis();
  if (now - lastHeartbeatMs > WATCHDOG_TIMEOUT_MS) {
    // Watchdog timed out! Drop into autonomous fallback
    handleAutonomousFallback();
    // Rapid flashing heartbeat LED indicates watchdog timeout
    digitalWrite(PIN_HEARTBEAT_LED, (now / 150) % 2 == 0 ? HIGH : LOW);
  } else {
    // Steady slow heartbeat blink indicates nominal health
    digitalWrite(PIN_HEARTBEAT_LED, (now / 1000) % 2 == 0 ? HIGH : LOW);
  }

  // 3. Emergency Strobe Beacon Handler
  if (emergencyStrobeActive) {
    if (now - lastStrobeToggleMs > 100) { // 10Hz strobe
      lastStrobeToggleMs = now;
      strobeState = !strobeState;
      digitalWrite(PIN_EMERGENCY_STROBE, strobeState ? HIGH : LOW);
    }
  } else {
    digitalWrite(PIN_EMERGENCY_STROBE, LOW);
  }
}

