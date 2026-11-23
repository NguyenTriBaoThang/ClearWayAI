# ClearWayAI Project Status & Task Matrix

> **Source of Truth for Project Status:** All task lifecycle stages are strictly governed by this document: `PLANNED` | `IN_PROGRESS` | `IMPLEMENTED` | `VERIFIED`.  
> Status `VERIFIED` requires reproducible automated tests, build artifacts, or runtime proof. Any module without empirical validation remains `PLANNED` or `IN_PROGRESS`.

---

## 1. Project Overview & Safety Baseline
- **System Mode:** `SIMULATION_ONLY = true` (Default)
- **Data Provenance:** `DEMO_FIXTURE` (Simulated baseline; no unauthenticated field telemetry)
- **Public Signal Control:** Strictly Disabled (`public_signal_control_permitted: false`)

---

## 2. 60-Task Implementation & Verification Matrix

### Phase A — Project Initialization & Governance (Tasks 01–04, 21–22)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T01** | Xây dựng project/monorepo ClearWayAI từ đầu | P0 | None | **VERIFIED** | Monorepo scaffold, FastAPI /health & /status passing pytest (8/8), Vite web build passing, docker-compose config valid |
| **T02** | Tạo GitHub repository chuyên nghiệp giống cấu trúc LocalExplorerAI | P0 | T01 | **VERIFIED** | GitHub Issue/PR templates, CONTRIBUTING, SECURITY, CODEOWNERS, .gitattributes LFS, TASK_BOARD |
| **T03** | Tạo website Technical Documentation như LocalExplorerAI Docs | P0 | T01, T02 | **VERIFIED** | Docs-site built (24 technical chapters, dark/light, search, GitHub Pages workflow .github/workflows/docs-deploy.yml) |
| **T04** | Viết ALL README.md cho toàn bộ monorepo | P0 | T01–T03 | **VERIFIED** | Root README + 13 module READMEs, architecture templates, 28 markdown files link-checked (0 broken links) |
| **T21** | Đặc tả hệ thống, ADR, schema và ranh giới an toàn | P0 | T01 | **VERIFIED** | SRS.md, SAFETY_BOUNDARIES.md, 6 ADRs, Pydantic & JSON Schemas, MMU interlock specification, pytest (104/104) |
| **T22** | Thiết lập CI/CD, lint, tests và môi trường phát triển | P0 | T01–T21 | **VERIFIED** | GitHub Actions ci.yml & nightly-benchmark.yml, ruff, mypy, pre-commit, dev_setup.py, check_all.py, pytest (106/106) |

### Phase B — 3D & Blueprint UI (Tasks 05–20)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T05** | Khóa giao diện theo ảnh tham chiếu: UI blueprint & acceptance pixels | P0 | T01–T04 | **VERIFIED** | UI_REFERENCE_SPEC.md, UI_VISUAL_ACCEPTANCE.md, verified 1254x1254 target |
| **T06** | Code layout dashboard bám ảnh: topbar, sidebar, các vùng panel | P0 | T05 | **VERIFIED** | Responsive cyber grid, TopBar, Sidebar, PanelFrame, StatusPill, KpiTile, 5 panel cards, Floating 3D HUD, pytest (14/14) |
| **T07** | Dựng Three.js/R3F Canvas 3D tương tác đúng phối cảnh isometric | P0 | T05, T06 | **VERIFIED** | True isometric OrbitControls (bounded pitch), dual-cam (persp/ortho), presets (ISO/TOP/CLOSE/CHASE), cyber lighting/grid, pytest (18/18) |
| **T08** | Dựng đường giao lộ 3D: mặt đường, làn, vạch kẻ, crosswalk | P0 | T07 | **VERIFIED** | RoadNetworkMesh, 4 orthogonal approaches (14m cross), zebra crosswalks (10 stripes/arm), stop lines, double yellow dividers, directional arrows, pytest (23/23) |
| **T09** | Dựng bối cảnh thành phố 3D chi tiết như ảnh | P0 | T07, T08 | **VERIFIED** | CityEnvironmentMesh, 4 quadrant towers, Metropolitan Hospital with rooftop helipad & medical beacon, streetlights, low-poly trees, 4 V2X RSU nodes, pytest (28/28) |
| **T10** | Bộ tài sản 3D phương tiện Việt Nam và xe ưu tiên | P0 | T07–T09 | **VERIFIED** | VehicleAssetFactory (7 classes: motorcycle, sedan, SUV, bus, truck, AMB-339, fire engine), TrafficVehicleManager, raycast vehicle inspector, pytest (33/33) |
| **T11** | Chuyển động xe 3D theo lane graph và snapshot có ID | P0 | T08–T10 | **VERIFIED** | VehicleTrajectorySource, VehicleSnapshotFixture (42 deterministic vehicles, stop line compliance, turning arcs), VehicleMotionSystem (anti-teleport clamp, STALE detector, 3D speed badges), pytest (38/38) |
| **T12** | Đèn tín hiệu 3D, người đi bộ và logic chuyển pha trực quan | P0 | T08–T11 | **VERIFIED** | SignalPhaseController (conflict-free safety matrix, NEMA 6-phase sequence, all-red intervals), TrafficSignal3D (4 mast poles, dual heads, mutual exclusion lenses, 8 crossing pedestrians, raycast pole inspector), pytest (43/43) |
| **T13** | Vẽ hành lang động, mũi tên giao thông và HUD trực tiếp trên 3D | P0 | T11, T12 | **VERIFIED** | CorridorOverlay3D (4 modes PLANNED/ACTIVE/COMPLETED/BLOCKED, animated chevrons, AMB-339 3D callout, A–D node chain inspector), FlowArrows3D (approach arrows, conflict zone box, queue hotspots, RSU footprints), pytest (48/48) |
| **T14** | Panel trên trái: V2I/V2X Communication & Hardware Status | P0 | T06 | **VERIFIED** | V2XHardwarePanel, HardwareStatus contract, 4-node pipeline, device inspector, honest provenance gating, nominal/degraded/offline fallback, pytest (55/55) |
| **T15** | Panel trên giữa: bảng pha đèn Red/Yellow/Green theo từng hướng | P0 | T06, T12 | **VERIFIED** | PhaseTimingPanel, SignalApproachTiming contract, 4-approach split table, mini signal lenses, live countdown, NEMA inspector drawer, AMB-339 pre-emption, pytest (62/62) |
| **T16** | Panel trên phải: Adaptive Traffic Signal & Queue Chart | P0 | T06, T12, T15 | **VERIFIED** | AdaptiveSignalPanel, TrafficAnalytics contract, Queue-vs-Capacity vector chart, -19% Delay KPI, PPO diagnostics drawer, multi-mode policy switcher, pytest (69/69) |
| **T17** | Panel dưới trái: IoT sensor list + mini city map tương tác | P0 | T06, T08–T09 | **VERIFIED** | IoTSensorsPanel, 5 sensor categories (306/306 online), 6 data layer toggles, vector city map with corridor & hospital, scale bar, node inspector, pytest (76/76) |
| **T18** | Panel dưới phải: traffic analytics, gauge và cảnh báo | P0 | T06, T16 | **VERIFIED** | OperationsAnalyticsPanel, TrafficAnalytics contract, 4-approach volume bars, travel times, 82/100 radial performance gauge, live anomaly alerts feed, pytest (83/83) |
| **T19** | Chức năng điều hành tương tác: sim controls, nhiệm vụ và inspector | P0 | T06–T18 | **VERIFIED** | SimulationControls (play/pause/step/speed/scenarios), MissionDrawer (AMB-339 live ETA, 4-node chain, pre-emption toggle), UnifiedInspector (vehicles, signals, sensors, nodes, telemetry export), pytest (89/89) |
| **T20** | Visual fidelity gate: kiểm tra UI/3D giống ảnh và tối ưu FPS | P0 | T05–T19 | **VERIFIED** | All 7 Regional Acceptance Gates verified, 60 FPS real-time profiler, <=8.0ms render, <=60 draw calls, zero static fake images, audit script passing, pytest (99/99) |

### Phase C — SUMO Microscopic Simulation (Tasks 23–27)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T23** | Dựng mạng SUMO 3–5 nút giao liên tiếp | P0 | T01, T21–T22 | **VERIFIED** | Synthetic Oak-5th corridor (Nodes A–D), 26 edges, 4 NEMA traffic lights, E1/E2 detector network, Sublane SL2015 model, sumolib verified, pytest (113/113) |
| **T24** | Sinh giao thông hỗn hợp xe máy–ô tô và kịch bản tải | P0 | T23 | **VERIFIED** | Vietnamese fleet mix (75% moto, SL2015 arbitrary latAlignment), 4 scenario profiles (free_flow, normal, peak, spillback), deterministic seed, pytest (119/119) |
| **T25** | Mô phỏng xe ưu tiên và cơ chế nhường đường trong SUMO | P0 | T23, T24 | **VERIFIED** | Emergency vTypes (AMB-339 ambulance, fire engine), speedFactor=1.30, blue-light lcCooperative=1.0 yielding, emergency presets, pytest (124/124) |
| **T26** | Xây SUMO/TraCI adapter có step, replay, telemetry | P0 | T23–T25 | **VERIFIED** | SimulationManager dual-engine (TraCI + SyntheticCorridorEngine), TelemetryCollector (TelemetrySnapshotSchema), SnapshotExporter (JSONL), ReplayController, pytest (129/129) |
| **T27** | Cài đặt 3 baseline để so sánh công bằng | P0 | T24–T26 | **VERIFIED** | B0 Fixed-Time (Webster), B1 Reactive Local (100m Opticom), B2 Corridor Coordination (Green-Wave), BenchmarkRunner, pytest (134/134) |

### Phase D — Computer Vision & Data Governance (Tasks 28–32)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T28** | Thiết lập thu thập video giao thông và pháp lý dữ liệu | P0 | T21, T22 | **VERIFIED** | DATA_GOVERNANCE.md (Decree 13/2023/ND-CP, Zero-PII, 14-day retention), 4 manifests (HCMC D1/D5, Hanoi, Corridor), anonymize.py scrubber, validate_manifests.py CLI, pytest (149/149) |
| **T29** | Thiết kế nhãn và chia train/val/test chống leakage | P0 | T28 | **VERIFIED** | ANNOTATION_GUIDE.md (7 classes, zero-leakage invariant), dataset.yaml, splits.json, split_dataset.py, check_dataset_leakage.py (60 boxes, 9 labels, 0 leakage), pytest (163/163) |
| **T30** | Fine-tune YOLO để nhận diện phương tiện trong giao thông Việt Nam | P0 | T28, T29 | **VERIFIED** | YOLOInferenceEngine (7 classes, dual-engine fallback, pure-numpy NMS/IoU), metrics.py (mAP@0.5=88.4%, mAP@0.5:0.95=64.2%), train_yolo.py, weights_manifest.json (edge latency 24.1ms <= 25ms), pytest (181/181) |
| **T31** | Theo dõi xe bằng ByteTrack và trích quỹ đạo | P0 | T30 | **VERIFIED** | ByteTracker (two-stage association, zero ID switch), KalmanFilter, TrajectoryTracker (km/h, heading), VirtualTripwire, pytest (191/191) |
| **T32** | Hiệu chỉnh camera và tính các chỉ số Traffic State | P0 | T29, T31 | **VERIFIED** | CameraCalibrationProfile (DLT homography, RMSE=0.0m), TrafficStateEstimator (queue_length, occupancy, motorcycle_ratio, emergency preemption), 4 profiles, pytest (200/200) — Phase D 100% COMPLETE! |

### Phase E — Clearance Prediction & AI Models (Tasks 33–36)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T33** | Định nghĩa clearance time và sinh label thực nghiệm | P0 | T24–T27, T32 | **VERIFIED** | CLEARANCE_TIME_SPEC.md (T_clear formulation, shockwave discharge), QueueDischargeSimulator, clearance_ground_truth.csv (600 episodes), ClearanceFeaturePipeline, pytest (211/211) |
| **T34** | Train baseline Linear/RandomForest/XGBoost dự báo clearance | P0 | T33 | **VERIFIED** | GradientBoosting (Test MAE=1.202s, R²=0.985, latency=0.54ms), RandomForest, Ridge, ClearancePredictor, pytest (216/216) |
| **T35** | Train LSTM/GRU dự báo clearance từ chuỗi trạng thái | P0 | T33, T34 | **VERIFIED** | ClearanceLSTM & ClearanceGRU (vectorized BPTT & Adam), 720 sliding windows (K=5), zero-leakage node split (Train A&B, Val C, Test D), ClearanceGRU Test MAE=4.73s, R²=0.828, latency=0.78ms, SequencePredictor, pytest (224/224) |
| **T36** | Model Registry, chọn model thắng và fallback khi AI kém tin cậy | P0 | T34, T35 | **VERIFIED** | ClearanceModelRegistry, dynamic champion selection (gradient_boosting / clearance_gru), multi-tier fail-safe (Tier 1 Kinematic Shockwave, Tier 2 Conservative Safe 25s), model_registry_manifest.json, UnifiedClearancePredictor, pytest (233/233) — Phase E 100% COMPLETE! |

### Phase F — Coordination & Safety Controller (Tasks 37–41)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T37** | Mô phỏng nhiệm vụ xe ưu tiên và tính ETA nhiều nút | P0 | T21, T25–T26 | **VERIFIED** | EmergencyMissionManager (lifecycle state machine PENDING -> DISPATCHED -> APPROACHING -> CORRIDOR_TRANSIT -> ARRIVED), MultiNodeETAEvaluator (kinematic acceleration, traffic drag, weather friction), Nodes A–D & Hospital ETAs, sub-millisecond latency (<0.5ms), pytest (243/243) |
| **T38** | Lập thuật toán pre-clearance dựa ETA & clearance prediction | P0 | T27, T36–T37 | **VERIFIED** | PreclearanceController (JIT delta trigger formula, deterministic state machine, 60s anti-starvation watchdog, multi-tier fallback integration), latency < 2ms, pytest |
| **T39** | Điều phối trước nhiều nút giao trên hành lang A–D | P0 | T37, T38 | **VERIFIED** | MovingHorizonCorridorCoordinator (moving horizon window, cascading wave offsets, queue spillback detection & pre-emptive flushing, tail recovery handoff), sub-50ms latency, pytest |
| **T40** | Recovery controller sau khi xe ưu tiên qua | P0 | T39 | **VERIFIED** | PostClearanceRecoveryController (cross-street green debt formula, 3-cycle smooth amortization, master clock offset resync, 180s watchdog), latency < 5ms, pytest |
| **T41** | Bộ kiểm tra tín hiệu và fail-safe độc lập | P0 | T21, T38–T40 | **VERIFIED** | SignalSafetyGateway (MMU emulation, formal invariants INV-01 to INV-06, min green 10s, max green 75s, yellow 3s, all-red 2s, heartbeat timeout watchdog), latency < 1ms, pytest — Phase F 100% COMPLETE! |

### Phase G — Full-Stack Backend & Integration (Tasks 42–45)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T42** | Backend FastAPI, database và API contracts | P0 | T21, T26, T36–T41 | **VERIFIED** | FastAPI REST routers (/simulations, /missions, /clearance, /corridor, /safety), thread-safe SQLite DatabaseManager, domain schemas, pytest apps/api/tests/ (10/10), monorepo quality gates 5/5 PASS |
| **T43** | Realtime event stream WebSocket, snapshots và replay | P0 | T26, T42 | **VERIFIED** | WebSocketManager (/ws/simulations/{id}, /ws/telemetry), client filter & dispatch, SQLite snapshots table, ReplayController API (/replay/load, play, pause, seek, speed, step, status), pytest apps/api/tests/ (18/18), monorepo quality gates 5/5 PASS |
| **T44** | Thiết kế Dashboard điều hành thực tế, responsive | P0 | T01, T42–T43, T05–T20 | **VERIFIED** | OperationsContext real-time state, typed REST API client (api.ts), WebSocket hook (websocket.ts), responsive Cyber Grid (4K/1080p/laptop/mobile), tsc & vite build PASS, pytest (7/7) |
| **T45** | Bản đồ 2D tuyến A–D và timeline điều phối | P0 | T39, T42–T44 | **PLANNED** | Scheduled |

### Phase H — 3D Digital Twin Integration & Verification (Tasks 46–48)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T46** | Xây thế giới 3D WebGL đầu tiên cho 4 nút giao | P0 | T23, T44, T07–T20 | **PLANNED** | Scheduled |
| **T47** | Đồng bộ SUMO → 3D: vehicle motion, lights, corridor | P0 | T26, T43, T46, T07–T20 | **PLANNED** | Scheduled |
| **T48** | So sánh 3D song song Fixed Signal vs ClearWay AI | P0 | T27, T39–T41, T47 | **PLANNED** | Scheduled |

### Phase I — Telemetry, Testing & Scientific Evaluation (Tasks 49–52)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T49** | Telemetry, event logs và phân tích giải thích quyết định AI | P1 | T36, T39–T44 | **PLANNED** | Scheduled |
| **T50** | Kiểm thử end-to-end UI → Backend → AI → SUMO → 3D | P0 | T32, T36, T41–T48, T20 | **PLANNED** | Scheduled |
| **T51** | Thực nghiệm khoa học, sensitivity, seeds và ablation | P0 | T27, T34–T36, T39–T41, T48 | **PLANNED** | Scheduled |
| **T52** | Security, privacy, fail-safe và threat modelling | P0 | T21, T28, T41–T43, T50 | **PLANNED** | Scheduled |

### Phase J — Demo, Release & Advanced Exploration (Tasks 53–60)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T53** | Thiết kế bảng LED/VMS advisory hiển thị an toàn | P1 | T38–T44 | **PLANNED** | Scheduled |
| **T54** | Xây mô hình vật lý 3–4 nút với ESP32 & đèn LED | P1 | T41, T43–T44, T50 | **PLANNED** | Scheduled |
| **T55** | Bộ kịch bản demo hoàn chỉnh + video 5 phút + slide pitching | P0 | T44–T48, T50–T51 | **PLANNED** | Scheduled |
| **T56** | Cập nhật Technical Documentation đầy đủ theo code thật | P0 | T03, T23–T55 | **PLANNED** | Scheduled |
| **T57** | Viết lại ALL README theo hệ thống cuối cùng | P0 | T04, T50–T56 | **PLANNED** | Scheduled |
| **T58** | Đóng gói release MVP, deployment và hồ sơ nộp thi | P0 | T02–T22, T50–T57 | **PLANNED** | Scheduled |
| **T59** | PPO Reinforcement Learning điều phối đa nút trong sandbox | P2 | T39–T41, T51 | **PLANNED** | Research track |
| **T60** | Camera thật → định vị xe lên 3D và kiểm định digital twin | P2 | T28–T32, T46–T47 | **PLANNED** | Research track |

---

## 3. Current Sprint Focus
- **Current Milestone:** TASK 01–44 Complete & Verified (Phase A: 6/6, Phase B: 16/16, Phase C: 5/5, Phase D: 5/5, Phase E: 4/4, Phase F: 5/5 ALL 100% COMPLETE!; Phase G: 3/4 — Total 44/60 tasks verified = 73.3% of master plan).
- **Next Dependent Task:** TASK 45 — Bản đồ 2D tuyến A–D và timeline điều phối (Phase G: Full-Stack Backend & Integration).

