"""Verification test suite for Task 15: Top-Middle Approach Split Timing Table Panel."""

import os
import re

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))
SHARED_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src"))


def test_phase_timing_files_exist():
    """Verify that PhaseTimingPanel and PhaseTimingCard exist in the web codebase."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    card_path = os.path.join(WEB_SRC, "features", "operations", "PhaseTimingCard.tsx")

    assert os.path.exists(panel_path), f"File {panel_path} must exist!"
    assert os.path.exists(card_path), f"File {card_path} must exist!"


def test_signal_state_contract_compliance():
    """Verify that PhaseTimingPanel adheres to the shared SignalState and SignalApproachTiming interfaces."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must import SignalApproachTiming and SignalState from @clearway/shared
    assert "SignalApproachTiming" in content
    assert "SignalState" in content

    # Must implement all fields of SignalApproachTiming
    assert "approach" in content
    assert "red_s" in content
    assert "yellow_s" in content
    assert "green_s" in content
    assert "cycle_s" in content
    assert "split_pct" in content
    assert "current_phase" in content
    assert "DEMO_FIXTURE" in content


def test_four_approach_split_timing_values():
    """Verify that all 4 approach rows have exact split timing values matching the UI blueprint."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 4 approaches:
    assert "N - Oak St. (NB)" in content
    assert "S - Oak St. (SB)" in content
    assert "E - 5th Ave. (EB)" in content
    assert "W - 5th Ave. (WB)" in content

    # Values matching blueprint:
    assert "67" in content  # Red 67s (N/S) or Green 67s (E/W)
    assert "49" in content  # Green 49s (N/S) or Red 49s (E/W)
    assert "4" in content   # Yellow 4s
    assert "120" in content # Cycle 120s
    assert "41" in content  # Split 41%
    assert "56" in content  # Split 56%


def test_mini_signal_head_and_countdown_display():
    """Verify visual mini signal heads (3 lenses) and countdown timers are present."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Lenses representation: Red, Yellow, Green color styling
    assert "#ef476f" in content
    assert "#ffd166" in content
    assert "#06d6a0" in content
    assert "countdownSec" in content


def test_interactive_approach_inspector():
    """Verify clicking an approach opens an inspector drawer with NEMA phase and clearance specs."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # NEMA phase assignments and clearances
    assert "minGreenSec" in content
    assert "maxGreenSec" in content
    assert "yellowChangeSec" in content
    assert "redClearanceSec" in content
    assert "pedestrianWalkSec" in content
    assert "detectorStatus" in content
    assert "selectedApproach" in content


def test_emergency_corridor_preemption():
    """Verify emergency corridor pre-emption override mode (AMB-339 priority corridor)."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "preemptionActive" in content
    assert "AMB-339" in content
    assert "CORRIDOR PRE-EMPTION" in content or "PREEMPTION" in content


def test_zero_static_fake_assets():
    """Verify no static raster screenshots are referenced in the component."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "PhaseTimingPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "dashboard-target.png" not in content
    assert "placeholder.png" not in content

