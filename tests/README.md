# ClearWayAI Automated Testing Suite (`tests`)

Houses root smoke tests, integration tests, and end-to-end (E2E) verification scripts.

---

## 1. Directory Structure

```
tests/
├── test_api_smoke.py       # Root API discovery and smoke checks
├── e2e/                    # Playwright end-to-end browser tests
├── integration/            # Multi-service integration tests (FastAPI + SUMO + Three.js)
└── README.md
```

---

## 2. Running Test Suites

```bash
# Run all Python unit & smoke tests
python -m pytest

# Run with verbose output and timing
python -m pytest -v --durations=10
```

---

## 3. Verification Gates

All pull requests must pass:
1. `pytest` unit & contract assertions (100% pass).
2. TypeScript strict checks across all frontend and shared packages.
3. Docker Compose configuration verification.
