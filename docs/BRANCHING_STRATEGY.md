# ClearWayAI Branching Strategy & Git Workflow

This document details the branch lifecycle, protection rules, and merge criteria for the ClearWayAI repository.

---

## 1. Branch Topology

```
main (Protected, Production Releases)
  ▲
  │ (Release PR, Tag: v0.1.0)
  │
develop (Protected, Integration)
  ▲
  │ (Pull Request with CI checks passed)
  │
feature/Txx-<name> | fix/<name> | exp/<name>
```

### 1.1 Branch Classifications

| Branch Type | Target Base | Naming Convention | Lifecycle | Protection Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Production** | None | `main` | Permanent | Requires PR review, linear history, CI passing |
| **Integration** | `main` | `develop` | Permanent | Requires PR review, CI passing |
| **Task Feature** | `develop` | `feature/Txx-<slug>` | Ephemeral | Deleted upon merge |
| **Bugfix** | `develop` | `fix/<issue-id>-<slug>`| Ephemeral | Deleted upon merge |
| **Hotfix** | `main` | `hotfix/v<x.y.z>` | Ephemeral | Merged into both `main` & `develop` |
| **Research/Exp**| `develop` | `exp/<experiment-id>` | Ephemeral | Documented in `EXPERIMENTS.md` |

---

## 2. Protected Branch Rules

### Rules for `main`:
1. **Require a Pull Request before merging:** Direct pushes are disabled.
2. **Require Status Checks to pass:**
   - Backend pytest suite (100% pass)
   - Frontend and shared packages build (`pnpm build`)
   - Linting check
3. **Require Linear History:** Prefer squash-and-merge or rebase-and-merge for clean atomic commits.
4. **Require Semantic Version Tagging:** Every release to `main` must carry a corresponding tag (`v0.1.0-alpha`, `v0.1.0-mvp`, etc.).

---

## 3. Step-by-Step Task Development Workflow

```bash
# 1. Update develop and branch for a specific task (e.g. Task 07)
git checkout develop
git pull origin develop
git checkout -b feature/T07-isometric-canvas

# 2. Work on your implementation and verify tests locally
python -m pytest
pnpm --filter clearway-web build

# 3. Commit with Conventional Commits
git add .
git commit -m "feat(3d): implement three.js isometric camera projection"

# 4. Push to remote origin
git push -u origin feature/T07-isometric-canvas

# 5. Open PR on GitHub targeting 'develop'
```

