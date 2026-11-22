# ClearWayAI Release Guide & Semantic Versioning

This document outlines the release lifecycle, versioning semantics, and step-by-step procedures for cutting releases in ClearWayAI.

---

## 1. Semantic Versioning Specification (SemVer 2.0.0)

ClearWayAI follows `MAJOR.MINOR.PATCH` with prerelease identifiers:

```
v0.1.0-alpha.1  ───► v0.1.0-mvp  ───► v1.0.0
 (Phase A–B)          (Phase C–I)      (Production)
```

- **MAJOR (x.0.0):** Breaking architectural changes, protocol rewrites, or API breaking changes.
- **MINOR (0.x.0):** New features, new simulation modules, or clearance models added in a backwards-compatible manner.
- **PATCH (0.0.x):** Bug fixes, performance optimizations, or documentation revisions.
- **Prerelease Suffixes:**
  - `-alpha`: Early development stage (UI scaffolds, initial simulation connectors).
  - `-beta`: Integrated end-to-end simulation with AI clearance models.
  - `-rc`: Release candidate undergoing benchmark validation.
  - `-mvp`: Minimum Viable Product tagged for competition demonstration and evaluation.

---

## 2. Release Checklist

Prior to publishing any tagged release:
- [ ] **Tests Green:** All unit, integration, and contract tests pass (`python -m pytest`).
- [ ] **Build Clean:** Production builds generate cleanly with no type errors (`pnpm build`).
- [ ] **Safety Audit:** Confirm `SIMULATION_ONLY=true` and `DATA_PROVENANCE` accurately labeled.
- [ ] **Status Matrix Updated:** All completed tasks marked `VERIFIED` in `docs/PROJECT_STATUS.md`.
- [ ] **Changelog Prepared:** Categorized summary of features, fixes, and known limitations.
- [ ] **Artifact Checksums:** Large model weights and dataset manifests have SHA256 checksums recorded.

---

## 3. Cutting a Release Step-by-Step

```bash
# 1. Ensure you are on main and working tree is clean
git checkout main
git pull origin main

# 2. Tag the release
git tag -a v0.1.0-alpha -m "Release v0.1.0-alpha: Monorepo scaffold, initial 3D engine, and GitHub governance"

# 3. Push tag to GitHub
git push origin v0.1.0-alpha

# 4. Draft GitHub Release using .github/release.yml automated generator
```

