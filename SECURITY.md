# Security & Safety Policy

## 1. Safety Ranh Giới (Operational Safety Boundaries)

ClearWayAI is developed as an intelligent traffic research platform and digital twin simulator. Because traffic control systems involve physical-world safety:

- **SIMULATION_ONLY Default:** All controller logic, AI decisions, and pre-clearance commands are hardcoded to execute within SUMO simulation or closed testbeds.
- **Fail-Safe Gateways:** Direct override of field traffic controllers is strictly prevented by software and policy. Any proposed signal phase must satisfy all safety invariants (conflict matrix, minimum green, mandatory yellow, and all-red clearance intervals).
- **Advisory Shadow Mode:** When connected to video feeds or recorded telemetry, the system acts strictly in advisory/shadow mode without actuation capability.

---

## 2. Data Privacy & Video Governance

- **No Raw PII:** Video datasets used for vehicle detection and clearance modeling must have identifiable personal data (faces, residential interiors, readable vehicle license plates) blurred or removed prior to storage.
- **No Unauthorized Surveillance:** Scraping or ingesting unauthenticated private camera feeds is strictly prohibited.
- **Dataset Manifests:** All training and evaluation datasets must maintain a cryptographic hash, license statement, and data governance record (`DATA_GOVERNANCE.md`).

---

## 3. Reporting Security Vulnerabilities

We take security and safe software design seriously. If you discover a potential vulnerability, safety violation, or credential leak in this project, please report it responsibly:

- **Email:** `security@clearway.ai` (or via private security advisory on GitHub).
- **Please Include:**
  - Description of the vulnerability.
  - Step-by-step reproduction instructions or proof-of-concept.
  - Potential impact on simulation sandboxing or safety mechanisms.

Please allow up to 48 hours for an initial response. Do **not** disclose security vulnerabilities publicly in GitHub Issues or pull requests before they have been evaluated and addressed.

---

## 4. Secrets Management

- Never commit API keys, database credentials, private keys, or `.env` files.
- The repository utilizes automated secret scanning and Dependabot alerts to continuously monitor dependencies and infrastructure.
