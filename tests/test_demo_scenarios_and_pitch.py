"""Automated Verification Suite for Demo Playbook, Video Script, Pitch Deck, and Demo Runner (Task 55).

Tests:
1. Documentation completeness and structural validation:
   - docs/DEMO_SCENARIOS.md (3 live scenarios, camera presets, presenter cues)
   - docs/VIDEO_DEMO_SCRIPT.md (6 acts, 00:00-05:00 timestamps, bilingual voiceover)
   - docs/PITCH_DECK.md (12-slide investor deck, empirical metrics, market sizing)
   - docs/DEFENSE_QA.md (16 technical Q&As across 4 categories)
2. Demo scenario runner execution:
   - Nominal arterial coordination
   - Emergency vehicle AMB-339 pre-clearance
   - Post-clearance resilient recovery
   - Full 3-act pipeline execution and demo_timeline.json export
"""

from __future__ import annotations

import json
from pathlib import Path

from simulation.experiments.demo_scenario_runner import DemoScenarioRunner


def test_demo_playbook_and_script_documentation_structure():
    """Verify presence and detailed structure of all 4 demo and presentation documents."""
    scenarios_doc = Path("docs/DEMO_SCENARIOS.md")
    video_doc = Path("docs/VIDEO_DEMO_SCRIPT.md")
    pitch_doc = Path("docs/PITCH_DECK.md")
    defense_doc = Path("docs/DEFENSE_QA.md")

    assert scenarios_doc.exists(), "docs/DEMO_SCENARIOS.md must exist"
    assert video_doc.exists(), "docs/VIDEO_DEMO_SCRIPT.md must exist"
    assert pitch_doc.exists(), "docs/PITCH_DECK.md must exist"
    assert defense_doc.exists(), "docs/DEFENSE_QA.md must exist"

    # 1. Scenarios content
    scenarios_text = scenarios_doc.read_text(encoding="utf-8")
    assert "Scenario 1: Nominal Arterial Green Wave" in scenarios_text
    assert "Scenario 2: Emergency Vehicle AMB-339" in scenarios_text
    assert "Scenario 3: Post-Clearance Resilient Recovery" in scenarios_text
    assert "CHASE" in scenarios_text and "TOP" in scenarios_text and "ISO" in scenarios_text
    assert "XE CỨU THƯƠNG ĐANG ĐẾN - DẠT PHẢI" in scenarios_text

    # 2. Video script content
    video_text = video_doc.read_text(encoding="utf-8")
    assert "00:00" in video_text and "05:00" in video_text
    assert "Scene 1: The Problem" in video_text
    assert "Scene 4: Live Demo — AMB-339 Emergency JIT Pre-clearance" in video_text
    assert "Voiceover (Vietnamese):" in video_text
    assert "Voiceover (English):" in video_text

    # 3. Pitch deck content
    pitch_text = pitch_doc.read_text(encoding="utf-8")
    assert "Slide 1: Title" in pitch_text
    assert "Slide 6: Empirical Evidence & Scientific Validation" in pitch_text
    assert "Slide 7: Physical Hardware Demonstration Testbench" in pitch_text
    assert "Slide 12: Call to Action" in pitch_text
    assert "-42.6%" in pitch_text

    # 4. Defense Q&A content
    defense_text = defense_doc.read_text(encoding="utf-8")
    assert "Q1: Why did you choose a Moving-Horizon" in defense_text
    assert "Q4: If the central server crashes" in defense_text
    assert "Decree 13/2023/ND-CP" in defense_text


def test_demo_scenario_runner_nominal():
    """Verify nominal peak-traffic coordination scenario execution."""
    runner = DemoScenarioRunner(output_path="simulation/experiments/test_timeline.json")
    res = runner.run_nominal_scenario(start_time=0.0, duration_sec=15.0)

    assert res["status"] == "SUCCESS"
    assert res["scenario"] == "NOMINAL_COORDINATION"
    assert len(runner.timeline) == 3
    assert runner.timeline[0].scenario == "NOMINAL_COORDINATION"
    assert runner.timeline[0].corridor_kpi["avg_delay_sec"] == 24.8


def test_demo_scenario_runner_emergency():
    """Verify AMB-339 emergency vehicle corridor pre-clearance scenario execution."""
    runner = DemoScenarioRunner(output_path="simulation/experiments/test_timeline.json")
    res = runner.run_emergency_scenario(start_time=15.0)

    assert res["status"] == "SUCCESS"
    assert res["scenario"] == "EMERGENCY_CORRIDOR"
    assert res["ev_id"] == "AMB-339"
    assert res["emergency_stops"] == 0
    assert res["travel_time_sec"] > 0

    # Ensure events contain valid EV positioning and VMS modes
    assert len(runner.timeline) > 0
    ev_event = runner.timeline[-1]
    assert ev_event.active_ev_id == "AMB-339"
    assert ev_event.ev_position_m is not None
    assert ev_event.ev_position_m >= 750.0


def test_demo_scenario_runner_recovery():
    """Verify post-clearance cross-street recovery scenario execution."""
    runner = DemoScenarioRunner(output_path="simulation/experiments/test_timeline.json")
    res = runner.run_recovery_scenario(start_time=80.0, duration_sec=15.0)

    assert res["status"] == "SUCCESS"
    assert res["scenario"] == "RECOVERY_COMPENSATION"
    assert len(runner.timeline) == 3
    assert runner.timeline[0].phase_name in ("ALL_EQUILIBRIUM", "RECOVERING")


def test_demo_scenario_runner_full_demonstration_and_artifact():
    """Verify full 3-act demonstration pipeline execution and JSON artifact creation."""
    artifact_path = Path("simulation/experiments/demo_timeline.json")
    runner = DemoScenarioRunner(output_path=str(artifact_path))

    full_res = runner.run_full_demonstration()

    assert artifact_path.exists(), "demo_timeline.json must be written to disk"
    assert full_res["total_events"] >= 15
    assert "nominal" in full_res["scenarios"]
    assert "emergency" in full_res["scenarios"]
    assert "recovery" in full_res["scenarios"]

    # Validate JSON structure
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert data["title"] == "ClearWayAI Master Demonstration Timeline"
    assert len(data["events"]) == full_res["total_events"]

    # Verify all events maintain valid hardware state
    for event in data["events"]:
        assert "hardware_state" in event
        assert "mode" in event["hardware_state"]
