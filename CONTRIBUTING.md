# Contributing to ClearWayAI

Thank you for your interest in contributing to **ClearWayAI**! We welcome contributions across our 3D Digital Twin, microscopic traffic simulations, computer vision pipelines, and multi-intersection coordination controllers.

---

## 1. Safety & Operational Constraints (Zero-Tolerance Rules)

ClearWayAI is a research and digital twin platform designed for traffic optimization and emergency corridor clearance. All contributions must adhere to the following strict safety guidelines:

1. **SIMULATION_ONLY by Default:** All control mechanisms operate exclusively within SUMO simulation sandboxes or isolated laboratory physical hardware.
2. **No Public Signal Manipulation:** Under no circumstances should code send unauthenticated or direct control signals to public roadside traffic infrastructure.
3. **Safety Gateway Invariants:** Any proposed traffic signal phase adjustment must pass through the Signal Safety Gateway:
   - Green conflicts are strictly rejected.
   - Yellow intervals and all-red clearance times cannot be bypassed or shortened.
   - Pedestrian clearance phases must be strictly respected.
4. **Data Provenance Honesty:** All mock, fixture, or synthetic data must be explicitly labeled (`DEMO_FIXTURE` or `SUMO_SIMULATED`). Never claim simulated sensors or metrics as live field telemetry.
5. **Privacy:** No unblurred human faces, identifiable license plates, or unauthorized camera streams may be committed to this repository.

---

## 2. Branching Strategy

Our branching model ensures stability, reproducibility, and rigorous code reviews:

```
main (protected) ───────────●──────────────────● (Releases: v0.1.0-alpha, etc.)
                            │                  ▲
develop ──────────●─────────┼────────●─────────┤ (Integration)
                  │         │        ▲         │
feature/Txx-* ────●─────────┴────────╯         │
```

- **`main`**: Production & release branch. Protected. Only merges from `develop` or release PRs after passing all CI gates.
- **`develop`**: Integration branch for ongoing task development.
- **`feature/Txx-<name>`**: Topic branch dedicated to a specific roadmap task (e.g. `feature/T07-3d-isometric-canvas`, `feature/T26-traci-adapter`).
- **`fix/<issue-id>`**: Bug fixes or hotfixes.
- **`exp/<experiment-id>`**: Experimental AI training runs or simulation ablation studies.

---

## 3. Commit Message Convention (Conventional Commits)

We enforce the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short description in present tense>

[optional body explaining motivation and context]

[optional footer referencing issue/task: Closes #12, Task: T07]
```

### Allowed Types:
- `feat`: A new feature or user-facing capability.
- `fix`: A bug fix in API, UI, simulation, or AI models.
- `3d`: Changes specific to Three.js / WebGL scene rendering.
- `sim`: SUMO network, demand scenarios, or TraCI adapters.
- `ai`: Computer vision, tracking, clearance prediction models.
- `safety`: Controller safety gateway, invariant checks, fail-safe.
- `docs`: Documentation, READMEs, technical specifications.
- `test`: Adding or refactoring unit, integration, or E2E tests.
- `chore`: Build scripts, dependencies, configuration updates.

---

## 4. Local Development Workflow

### Prerequisites
- Python 3.10+ (with `pip`)
- Node.js 18+ and `pnpm` 9+ (or `npm`)
- Eclipse SUMO (for simulation tasks)
- Git (with Git LFS installed)

### Setup
```bash
# 1. Clone repository
git clone https://github.com/NguyenTriBaoThang/ClearWayAI.git
cd ClearWayAI

# 2. Windows PowerShell Bootstrap
.\scripts\bootstrap.ps1

# Or Linux Bash Bootstrap
./scripts/bootstrap.sh
```

### Running Tests Locally
Before opening a pull request, verify all automated tests pass:
```bash
# Python backend smoke & unit tests
python -m pytest

# TypeScript packages & frontend build
pnpm --filter @clearway/shared build
pnpm --filter clearway-web build

# Docker Compose validation
docker-compose config
```

---

## 5. Pull Request Process

1. Open your PR against `develop` (or `main` if single-branch model applies).
2. Fill out the complete [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).
3. Ensure all automated tests and typechecks pass.
4. Attach visual evidence (screenshots, terminal logs, or screen recordings) for any UI or 3D changes.
5. Update `docs/PROJECT_STATUS.md` and module documentation if your PR completes or progresses a roadmap task.

