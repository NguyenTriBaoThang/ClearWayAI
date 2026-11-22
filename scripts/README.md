# ClearWayAI Automation & Developer Scripts (`scripts`)

Utility scripts for environment bootstrap, data ingestion, and testing automation.

---

## 1. Directory Structure

```
scripts/
├── bootstrap.ps1           # Windows PowerShell automated setup script
├── bootstrap.sh            # Linux/macOS Bash automated setup script
├── prepare_demo.py         # Script to preload verified scenario and seed fixtures
└── README.md
```

---

## 2. Usage

### Automated Bootstrap:
```powershell
# Windows
.\scripts\bootstrap.ps1

# Linux
./scripts/bootstrap.sh
```

These scripts verify Python 3.10+, Node.js 18+, package managers, copy `.env.example` to `.env`, and install dependencies automatically.

