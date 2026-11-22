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
| **T02** | Tạo GitHub repository chuyên nghiệp giống cấu trúc LocalExplorerAI | P0 | T01 | **PLANNED** | Scheduled next |
| **T03** | Tạo website Technical Documentation như LocalExplorerAI Docs | P0 | T01, T02 | **PLANNED** | Scheduled |
| **T04** | Viết ALL README.md cho toàn bộ monorepo | P0 | T01–T03 | **PLANNED** | Scheduled |
| **T21** | Đặc tả hệ thống, ADR, schema và ranh giới an toàn | P0 | T01 | **PLANNED** | Scheduled |
| **T22** | Thiết lập CI/CD, lint, tests và môi trường phát triển | P0 | T01–T21 | **PLANNED** | Scheduled |

### Phase B — 3D & Blueprint UI (Tasks 05–20)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T05** | Khóa giao diện theo ảnh tham chiếu: UI blueprint & acceptance pixels | P0 | T01–T04 | **PLANNED** | assets/reference/dashboard-target.png copied (1254x1254) |
| **T06** | Code layout dashboard bám ảnh: topbar, sidebar, các vùng panel | P0 | T05 | **PLANNED** | Scheduled |
| **T07** | Dựng Three.js/R3F Canvas 3D tương tác đúng phối cảnh isometric | P0 | T05, T06 | **PLANNED** | Scheduled |
| **T08** | Dựng đường giao lộ 3D: mặt đường, làn, vạch kẻ, crosswalk | P0 | T07 | **PLANNED** | Scheduled |
| **T09** | Dựng bối cảnh thành phố 3D chi tiết như ảnh | P0 | T07, T08 | **PLANNED** | Scheduled |
| **T10** | Bộ tài sản 3D phương tiện Việt Nam và xe ưu tiên | P0 | T07–T09 | **PLANNED** | Scheduled |
| **T11** | Chuyển động xe 3D theo lane graph và snapshot có ID | P0 | T08–T10 | **PLANNED** | Scheduled |
| **T12** | Đèn tín hiệu 3D, người đi bộ và logic chuyển pha trực quan | P0 | T08–T11 | **PLANNED** | Scheduled |
| **T13** | Vẽ hành lang động, mũi tên giao thông và HUD trực tiếp trên 3D | P0 | T11, T12 | **PLANNED** | Scheduled |
| **T14** | Panel trên trái: V2I/V2X Communication & Hardware Status | P0 | T06 | **PLANNED** | Scheduled |
| **T15** | Panel trên giữa: bảng pha đèn Red/Yellow/Green theo từng hướng | P0 | T06, T12 | **PLANNED** | Scheduled |
| **T16** | Panel trên phải: Adaptive Traffic Signal & Queue Chart | P0 | T06, T12, T15 | **PLANNED** | Scheduled |
| **T17** | Panel dưới trái: IoT sensor list + mini city map tương tác | P0 | T06, T08–T09 | **PLANNED** | Scheduled |
| **T18** | Panel dưới phải: traffic analytics, gauge và cảnh báo | P0 | T06, T16 | **PLANNED** | Scheduled |
| **T19** | Chức năng điều hành tương tác: sim controls, nhiệm vụ và inspector | P0 | T06–T18 | **PLANNED** | Scheduled |
| **T20** | Visual fidelity gate: kiểm tra UI/3D giống ảnh và tối ưu FPS | P0 | T05–T19 | **PLANNED** | Scheduled |

### Phase C — SUMO Microscopic Simulation (Tasks 23–27)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T23** | Dựng mạng SUMO 3–5 nút giao liên tiếp | P0 | T01, T21–T22 | **PLANNED** | Scheduled |
| **T24** | Sinh giao thông hỗn hợp xe máy–ô tô và kịch bản tải | P0 | T23 | **PLANNED** | Scheduled |
| **T25** | Mô phỏng xe ưu tiên và cơ chế nhường đường trong SUMO | P0 | T23, T24 | **PLANNED** | Scheduled |
| **T26** | Xây SUMO/TraCI adapter có step, replay, telemetry | P0 | T23–T25 | **PLANNED** | Scheduled |
| **T27** | Cài đặt 3 baseline để so sánh công bằng | P0 | T24–T26 | **PLANNED** | Scheduled |

### Phase D — Computer Vision & Data Governance (Tasks 28–32)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T28** | Thiết lập thu thập video giao thông và pháp lý dữ liệu | P0 | T21, T22 | **PLANNED** | Scheduled |
| **T29** | Thiết kế nhãn và chia train/val/test chống leakage | P0 | T28 | **PLANNED** | Scheduled |
| **T30** | Fine-tune YOLO để nhận diện phương tiện trong giao thông Việt Nam | P0 | T28, T29 | **PLANNED** | Scheduled |
| **T31** | Theo dõi xe bằng ByteTrack và trích quỹ đạo | P0 | T30 | **PLANNED** | Scheduled |
| **T32** | Hiệu chỉnh camera và tính các chỉ số Traffic State | P0 | T29, T31 | **PLANNED** | Scheduled |

### Phase E — Clearance Prediction & AI Models (Tasks 33–36)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T33** | Định nghĩa clearance time và sinh label thực nghiệm | P0 | T24–T27, T32 | **PLANNED** | Scheduled |
| **T34** | Train baseline Linear/RandomForest/XGBoost dự báo clearance | P0 | T33 | **PLANNED** | Scheduled |
| **T35** | Train LSTM/GRU dự báo clearance từ chuỗi trạng thái | P0 | T33, T34 | **PLANNED** | Scheduled |
| **T36** | Model Registry, chọn model thắng và fallback khi AI kém tin cậy | P0 | T34, T35 | **PLANNED** | Scheduled |

### Phase F — Coordination & Safety Controller (Tasks 37–41)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T37** | Mô phỏng nhiệm vụ xe ưu tiên và tính ETA nhiều nút | P0 | T21, T25–T26 | **PLANNED** | Scheduled |
| **T38** | Lập thuật toán pre-clearance dựa ETA & clearance prediction | P0 | T27, T36–T37 | **PLANNED** | Scheduled |
| **T39** | Điều phối trước nhiều nút giao trên hành lang A–D | P0 | T37, T38 | **PLANNED** | Scheduled |
| **T40** | Recovery controller sau khi xe ưu tiên qua | P0 | T39 | **PLANNED** | Scheduled |
| **T41** | Bộ kiểm tra tín hiệu và fail-safe độc lập | P0 | T21, T38–T40 | **PLANNED** | Scheduled |

### Phase G — Full-Stack Backend & Integration (Tasks 42–45)
| Task ID | Task Description | Priority | Dependencies | Status | Verification Proof |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T42** | Backend FastAPI, database và API contracts | P0 | T21, T26, T36–T41 | **PLANNED** | Initial API live in T01 |
| **T43** | Realtime event stream WebSocket, snapshots và replay | P0 | T26, T42 | **PLANNED** | Scheduled |
| **T44** | Thiết kế Dashboard điều hành thực tế, responsive | P0 | T01, T42–T43, T05–T20 | **PLANNED** | Shell ready |
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
- **Current Milestone:** TASK 01 Complete & Verified.
- **Next Dependent Task:** TASK 02 — Tạo GitHub repository chuyên nghiệp giống cấu trúc LocalExplorerAI.
