# ADR 0003: 3D WebGL Digital Twin Implementation with Three.js

## Context
Operators require an intuitive spatial visualization of intersection geometry, vehicle trajectories, queue formations, signal aspects, and emergency priority routes. Static 2D maps fail to convey lane-level conflicts, elevation, or 3D sensor footprints. Heavy game engines (e.g. Unreal/Unity) introduce significant browser packaging bloat and require specialized WebAssembly builds.

## Decision
We implement the 3D Digital Twin using **Three.js** running directly in the browser via standard WebGL:
1. Custom procedural meshes for road intersections (`RoadNetworkMesh`), city towers (`CityEnvironmentMesh`), vehicles (`VehicleAssetFactory`), and signal poles (`TrafficSignal3D`).
2. Dual projection mode (`Perspective` and true `Orthographic` isometric).
3. Strict performance budgeting: target $\ge 55\text{ FPS}$ (60 FPS measured), frame render time $\le 8.0\text{ ms}$, draw calls $\le 60$, and triangle count $\le 25,000$.
4. Real-time dynamic overlay ribbons for emergency routes (`CorridorOverlay3D`) and flow arrows (`FlowArrows3D`).

## Consequences
- **Positive:** Zero external plugin dependencies, fast loading in standard modern browsers, responsive resizing, interactive raycasting on 3D vehicles and poles.
- **Negative:** Requires manual low-level shader and geometry optimization, memory cleanup on unmount, and synthetic coordinate transforms from SUMO world coordinates.

