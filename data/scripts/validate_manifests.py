"""ClearWayAI Manifest Validation Suite.

Validates JSON video ingestion manifests against the Data Governance standard
and asserts compliance with Vietnam's Decree No. 13/2023/ND-CP on Personal Data Protection.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LocationSpec(BaseModel):
    """Geographic and roadside deployment metadata."""

    city: str
    district: str
    intersection_name: str
    camera_id: str
    gps_coordinates: list[float] = Field(..., min_length=2, max_length=2)


class TimePeriodSpec(BaseModel):
    """Observation period and temporal category."""

    start_utc: str
    end_utc: str
    time_of_day: Literal["morning_peak", "evening_peak", "midday", "night", "peak", "off_peak"]


class VideoSpec(BaseModel):
    """Optical and encoding technical specifications."""

    resolution: list[int] = Field(..., min_length=2, max_length=2)
    fps: float = Field(..., gt=0.0)
    duration_seconds: float = Field(..., gt=0.0)
    format: str = "mp4"
    codec: str = "h264"


class PrivacyComplianceSpec(BaseModel):
    """Decree 13/2023/ND-CP Personal Data Protection compliance flags."""

    face_blurred: bool
    license_plate_blurred: bool
    decree_13_compliant: bool
    anonymizer_version: str


class IntegritySpec(BaseModel):
    """Cryptographic chain-of-custody checksums."""

    sha256_raw: str
    sha256_anonymized: str
    file_size_bytes: int = Field(..., gt=0)

    @field_validator("sha256_raw", "sha256_anonymized")
    @classmethod
    def validate_sha256_hex(cls, v: str) -> str:
        if not re.fullmatch(r"^[0-9a-fA-F]{64}$", v):
            raise ValueError(f"Invalid SHA-256 digest: must be 64 hexadecimal characters, got '{v}'")
        return v.lower()


class TrafficCharacteristicsSpec(BaseModel):
    """Dominant roadway flow and mixed motorcycle traffic statistics."""

    dominant_vehicle: str
    motorcycle_percentage: float = Field(..., ge=0.0, le=100.0)
    estimated_density: Literal["low", "medium", "high", "spillback"]
    estimated_flow_rate_vph: int = Field(..., ge=0)


class VideoManifest(BaseModel):
    """Root metadata schema for traffic video ingestion under ClearWayAI governance."""

    manifest_version: str
    video_id: str
    provenance: Literal[
        "OFFLINE_VIDEO",
        "SUMO_SIMULATED",
        "DEMO_FIXTURE",
        "SHADOW_ADVISORY",
        "LIVE_CONNECTED",
    ]
    location: LocationSpec
    time_period: TimePeriodSpec
    weather_condition: Literal["clear", "overcast", "rain", "haze"]
    video_spec: VideoSpec
    privacy_compliance: PrivacyComplianceSpec
    integrity: IntegritySpec
    traffic_characteristics: TrafficCharacteristicsSpec

    def validate_decree13_invariants(self) -> list[str]:
        """Assert legal compliance with Decree 13/2023/ND-CP."""
        errors: list[str] = []
        if self.provenance == "OFFLINE_VIDEO":
            if not self.privacy_compliance.face_blurred:
                errors.append("Decree 13 violation: OFFLINE_VIDEO must have face_blurred = True")
            if not self.privacy_compliance.license_plate_blurred:
                errors.append(
                    "Decree 13 violation: OFFLINE_VIDEO must have license_plate_blurred = True"
                )
            if not self.privacy_compliance.decree_13_compliant:
                errors.append(
                    "Decree 13 violation: OFFLINE_VIDEO must have decree_13_compliant = True"
                )
        return errors


def validate_manifest_file(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a single JSON manifest file."""
    errors: list[str] = []
    if not file_path.is_file():
        return False, [f"Manifest file not found: {file_path}"]

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return False, [f"JSON parsing error in {file_path.name}: {exc}"]

    try:
        manifest = VideoManifest.model_validate(data)
    except Exception as exc:
        return False, [f"Schema validation error in {file_path.name}: {exc}"]

    legal_errors = manifest.validate_decree13_invariants()
    if legal_errors:
        errors.extend(legal_errors)

    return len(errors) == 0, errors


def validate_directory(dir_path: Path) -> tuple[int, int, list[str]]:
    """Validate all manifest files in a directory.

    Returns:
        (total_checked, total_passed, all_errors)
    """
    json_files = sorted(dir_path.glob("*.json"))
    if not json_files:
        return 0, 0, [f"No JSON manifests found in {dir_path}"]

    passed = 0
    all_errors: list[str] = []

    for f in json_files:
        ok, errs = validate_manifest_file(f)
        if ok:
            passed += 1
        else:
            all_errors.extend(f"{f.name}: {e}" for e in errs)

    return len(json_files), passed, all_errors


def main() -> int:
    """CLI runner for manifest validation."""
    parser = argparse.ArgumentParser(
        description="ClearWayAI Video Ingestion Manifest Validator (Decree 13/2023/ND-CP)"
    )
    parser.add_argument(
        "--manifest-dir",
        type=str,
        default="data/manifests",
        help="Directory containing video manifest JSON files",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Validate a single manifest file",
    )
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        ok, errors = validate_manifest_file(path)
        if ok:
            print(f"[OK] Manifest {path.name} passed validation.")
            return 0
        else:
            print(f"[FAIL] Manifest {path.name} failed validation:")
            for err in errors:
                print(f"  - {err}")
            return 1

    manifest_dir = Path(args.manifest_dir)
    total, passed, errors = validate_directory(manifest_dir)

    print(f"Validated {passed}/{total} manifest(s) in {manifest_dir}.")
    if errors:
        print(f"Found {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[SUCCESS] All video manifests comply with ClearWayAI Data Governance and Decree 13.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

