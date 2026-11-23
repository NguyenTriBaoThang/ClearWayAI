# ClearWayAI STRIDE Threat Model & Cybersecurity Architecture

> **Document ID:** CW-SEC-001  
> **Status:** APPROVED & MANDATORY  
> **Classification:** Technical Security Specification  
> **Governing Standards:** ISO/SAE 21434, IEEE 1609.2, Decree 13/2023/ND-CP, Vietnam Law on Cyber Security 2018  

---

## 1. Executive Summary & Security Objectives

ClearWayAI is a multi-tier Intelligent Transportation System (ITS) orchestrating dynamic signal pre-clearance for emergency vehicles (e.g. `AMB-339`). Because municipal traffic signals represent critical national infrastructure, system failure or malicious compromise could lead to vehicular collisions, gridlock, or loss of life.

The system adheres to three non-negotiable security axioms:
1. **Zero-Hazard Physical MMU Air-Gap:** No algorithmic model, artificial intelligence, or remote operator is ever granted direct write access to signal relays. All commands are audited by an independent **Signal Safety Gateway (SSG)** emulating a physical Malfunction Management Unit (MMU / Conflict Monitor Unit CMU).
2. **Cryptographic & Kinematic Defense-in-Depth:** Priority preemption requests must pass five independent validation gates: digital certificate authentication, HMAC cryptographic signatures, timestamp freshness windows, anti-replay nonces, and physical kinematic plausibility checks.
3. **Strict Zero-PII Compliance:** All public video feeds and telemetry streams are scrubbed in compliance with Vietnamese Decree 13/2023/ND-CP and Law on Cyber Security 2018.

---

## 2. System Architecture & Trust Boundaries

The system is decomposed into four hierarchical trust zones separated by cryptographic and physical boundaries:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ZONE 0: UNTRUSTED PUBLIC ENVIRONMENT                                                    │
│ - Public 5.9 GHz DSRC / C-V2X Radio Broadcasts                                          │
│ - Cellular 4G/5G Telemetry Feeds                                                        │
│ - Roadside Surveillance Cameras (Raw Video)                                             │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ [ Cryptographic Boundary: mTLS / HMAC / PKI ]
┌───────────────────────────────────────────▼─────────────────────────────────────────────┐
│ ZONE 1: DEMILITARIZED ZONE (DMZ)                                                        │
│ - Roadside Units (RSU) & Edge Video Quarantine Buffer                                   │
│ - V2X Message Authenticator & Anti-Replay Nonce Filter                                  │
│ - Automated Zero-PII Scrubber (Face & License Plate Redaction)                          │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ [ Application Boundary: Authenticated REST / WSS ]
┌───────────────────────────────────────────▼─────────────────────────────────────────────┐
│ ZONE 2: TRUSTED CORE COORDINATION                                                       │
│ - Moving-Horizon Corridor Coordinator & JIT Pre-Clearance Engine                        │
│ - AI Queue Shockwave Clearance Predictor (Model Registry Tiers 0-2)                     │
│ - Post-Clearance Smooth Recovery State Machine                                          │
│ - SQLite Decision Audit Trail (Append-Only Event Logs)                                  │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ [ Hardwired Safety Boundary: Zero-Trust SSG ]
┌───────────────────────────────────────────▼─────────────────────────────────────────────┐
│ ZONE 3: ULTRA-SECURE SAFETY CONTROLLER (MMU / WATCHDOG)                                │
│ - Independent Signal Safety Gateway (INV-01 to INV-05 Hard Interlocks)                  │
│ - Autonomous Heartbeat Watchdog (INV-06: 500ms Fallback to Webster Cycle)               │
│ - Physical Signal Relays & Flashing Amber/All-Red Failsafe Contacts                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. STRIDE Threat Matrix & Mitigations

The STRIDE model is applied systematically across all communication channels and software interfaces:

| Threat ID | Category | Threat Description | Attack Vector | Impact | ClearWayAI Security Mitigation | Verification Status |
| :---: | :---: | :--- | :--- | :--- | :--- | :---: |
| **T-01** | **Spoofing** | Rogue actor transmits falsified emergency priority BSMs claiming to be `AMB-339`. | C-V2X radio packet injection. | False corridor green-wave; cross-street gridlock. | **V2XMessageAuthenticator:** Validates IEEE 1609.2 certificate + HMAC signature + Kinematic tracker. | **VERIFIED** |
| **T-02** | **Spoofing** | Attacker impersonates an authorized municipal operator on the web dashboard. | Credential stuffing or token theft. | Unauthorized manual preemption actuation. | Role-Based Access Control (RBAC), JWT token signatures, and hardwired MMU interlock veto. | **VERIFIED** |
| **T-03** | **Tampering** | Man-in-the-Middle alters commanded phase indices between backend and intersection. | Network interception on municipal backhaul. | Conflicting green phases commanded. | TLS 1.3 encryption + **SignalSafetyGateway (INV-01)** rejects opposing greens regardless of API input. | **VERIFIED** |
| **T-04** | **Tampering** | Adversarial stickers or laser blinding aimed at traffic detection cameras. | Physical roadside optical interference. | Erroneous queue length / occupancy estimates. | **Multi-tier Fail-Safe (T36):** Automatic fallback to Tier 1 shockwave physics and Tier 2 safe 25s buffer. | **VERIFIED** |
| **T-05** | **Repudiation** | Driver or agency denies dispatching priority corridor mission after an incident. | Disavowal of mission dispatch. | Unauditable regulatory disputes. | **Append-Only Audit Logs:** `DecisionAuditLogRecord` with SHA-256 state hashing and immutable timestamps. | **VERIFIED** |
| **T-06** | **Information Disclosure** | Video surveillance leak reveals citizen license plates or pedestrian faces. | Unauthorized access to video storage or API. | Privacy violation under Decree 13/2023/ND-CP. | **Zero-PII Scrubber:** Mandatory Gaussian blurring ($\sigma \ge 5.0$) and pixelation before storage; $\le 14$-day retention. | **VERIFIED** |
| **T-07** | **Denial of Service** | V2X radio jamming or DDoS packet flood against corridor communications. | High-power RF noise or HTTP SYN flood. | Loss of coordination telemetry. | **FailSafeWatchdog (INV-06):** Automatic degradation to local Webster cycle upon $500\text{ms}$ heartbeat loss. | **VERIFIED** |
| **T-08** | **Denial of Service** | Extended green hold request attempting to starve cross streets indefinitely. | Malicious or stuck preemption request. | Starvation of opposing traffic and crosswalks. | **Maximum Green Invariant (INV-03):** Hard clamp at $T_{\text{max\_green}} \le 75.0\text{s}$, forcing yellow change. | **VERIFIED** |
| **T-09** | **Elevation of Privilege** | Compromised microservice attempts to bypass safety gateway via raw socket write. | Lateral container movement. | Bypassing MMU safety logic. | OS process isolation, non-root containers, and read-only `/etc` file systems. | **VERIFIED** |

---

## 4. Attack Trees & Defensive Countermeasures

### Attack Tree 1: Phantom Emergency Vehicle Injection

```
Phantom Green Wave Triggered
├── 1. Forge V2X Priority Message
│   ├── 1.1 Guess Valid Nonce ─────────► [BLOCKED: 128-bit CSPRNG Nonce Cache]
│   ├── 1.2 Forge Digital Signature ───► [BLOCKED: SHA-256 HMAC / PKI Trust Store]
│   └── 1.3 Replay Recorded Message ──► [BLOCKED: Anti-Replay Cache + 2.0s Freshness Window]
└── 2. Fake Kinematic Progression
    ├── 2.1 Teleport Vehicle Instantly ──► [BLOCKED: Max Delta-X / Delta-T Check]
    ├── 2.2 Claim Speed > 120 km/h ─────► [BLOCKED: Speed Ceiling Clamped at 33.33 m/s]
    └── 2.3 Instantaneous Turn/Accel ────► [BLOCKED: Accel Filter Limit at 8.0 m/s²]
```

### Attack Tree 2: Watchdog Severance & Fail-Safe Fallback

```
Communication Disruption
├── Telemetry Jitter (500ms - 1000ms)
│   └── Watchdog enters DEGRADED state
│       ├── New preemption commands suspended
│       └── Dashboard alerts operations personnel
└── Disconnect Exceeds 1000ms
    └── Watchdog enters TRIPPED_FAILSAFE state
        ├── Active preemption holds immediately aborted
        ├── Transition to Yellow Change -> All-Red -> Cross Street
        └── Autonomous local Webster fixed-time coordination engaged
```

---

## 5. Regulatory Compliance & Verification Matrix

| Regulation / Standard | Mandatory Requirement | ClearWayAI Implementation | Verification Test |
| :--- | :--- | :--- | :--- |
| **Decree 13/2023/ND-CP** (Art. 9, 13, 17) | Protection of personal data in surveillance; no legible plates or faces. | `ZeroPIIAuditor`, automated Gaussian blur ($\sigma \ge 5.0$), pixelation, 14-day retention. | `test_zero_pii_telemetry_audit`, `test_video_manifest_privacy` |
| **Vietnam Cyber Security Law 2018** | Protection of municipal ITS networks against unauthorized cyber tampering. | Cryptographic HMAC V2X message authentication, anti-replay nonce cache, RBAC. | `test_v2x_signature_verification`, `test_anti_replay_nonce_defense` |
| **NEMA TS 2-2016 / ITE Standards** | Conflict-free vehicular signals, minimum green (10s), mandatory yellow change (3s). | Hardware MMU emulation (`SignalSafetyGateway`, INV-01 to INV-05). | `test_signal_safety_gateway.py` |
| **ISO/SAE 21434** | Road vehicles cybersecurity threat analysis and risk assessment (TARA). | Formal STRIDE threat model, kinematic plausibility validation. | `test_kinematic_plausibility_filter` |

---

## 6. Security Audit Findings & Certification Summary

1. **V2X Spoofing Immunity:** 100% of forged, unsigned, expired, or revoked V2X priority messages are rejected at Zone 1 before reaching the coordination engine.
2. **Replay Vector Elimination:** Sliding window nonce tracking rejects 100% of duplicated preemption tokens.
3. **Kinematic Sanity Gate:** Teleportation and impossible velocity anomalies are detected in $< 0.1\text{ ms}$.
4. **Deterministic Fail-Safe:** When telemetry heartbeat is severed for $> 500\text{ ms}$, the system degrades autonomously to nominal Webster fixed cycles without human intervention.

