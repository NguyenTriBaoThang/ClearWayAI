# ADR 0001: Monorepo Structure with pnpm Workspaces & FastAPI

## Context
ClearWayAI combines multiple distinct disciplines:
1. Microscopic traffic simulation (Python / TraCI / SUMO).
2. Deep learning perception (PyTorch / YOLOv8 / ByteTrack).
3. Backend API & coordination gateway (FastAPI / WebSockets / Redis).
4. Real-time 3D WebGL Digital Twin and operations dashboard (TypeScript / React / Three.js).
5. Technical documentation portal (Vite / React / Markdown).

Managing these across separate git repositories creates version synchronization drift, fragmented CI/CD, and dependency mismatch across shared data schemas.

## Decision
We adopt a unified **polyglot monorepo structure** managed by `pnpm` workspaces for frontend packages and standard Python virtual environments / Docker for backend services:
- `apps/web`: React + Vite + Three.js operations dashboard.
- `apps/api`: FastAPI REST + WebSocket telemetry server.
- `apps/docs-site`: Technical documentation portal.
- `packages/shared`: Shared TypeScript type definitions and JSON schemas.
- `docker-compose.yml`: Unified local orchestration.

## Consequences
- **Positive:** Atomic cross-cutting commits, shared types between frontend and backend, single source of truth for CI/CD and verification.
- **Negative:** Requires multi-language toolchains (Node.js + Python), careful path aliasing in TypeScript, and coordinated container builds.

