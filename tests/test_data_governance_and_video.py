"""Automated verification suite for Task 28: Data Governance, Video Ingestion & Privacy Scrubber.

Validates adherence to Decree 13/2023/ND-CP, JSON manifest schema integrity,
cryptographic SHA-256 digests, and anonymization algorithms.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from data.scripts.anonymize import (
    ANONYMIZER_VERSION,
    BoundingBox,
    PrivacyScrubber,
    apply_gaussian_blur,
    apply_pixelation,
    apply_solid_mask,
    compute_sha256,
    verify_manifest_decree13,
)
from data.scripts.validate_manifests import (
    VideoManifest,
    validate_directory,
    validate_manifest_file,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def manifests_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "manifests"


# =========================================================================
# 1. DATA GOVERNANCE DOCUMENT COMPLIANCE TESTS
# =========================================================================


def test_data_governance_document_exists_and_compliant(repo_root: Path) -> None:
    """Assert docs/DATA_GOVERNANCE.md exists and documents mandatory compliance requirements."""
    doc_path = repo_root / "docs" / "DATA_GOVERNANCE.md"
    assert doc_path.is_file(), f"Expected governance document at {doc_path}"

    content = doc_path.read_text(encoding="utf-8")

    # Mandatory legal references
    assert "13/2023/ND-CP" in content
    assert "Cyber Security" in content or "Cybersecurity" in content

    # Zero-PII principles
    assert "Zero-PII" in content or "Zero PII" in content
    assert "face" in content.lower()
    assert "license plate" in content.lower()

    # Retention rules
    assert "14" in content
    assert "days" in content.lower()

    # Cryptographic integrity
    assert "SHA-256" in content or "sha256" in content.lower()

    # Provenance tags
    assert "OFFLINE_VIDEO" in content
    assert "SUMO_SIMULATED" in content


# =========================================================================
# 2. MANIFEST DIRECTORY & SCHEMA INTEGRITY TESTS
# =========================================================================


def test_standard_manifests_exist(manifests_dir: Path) -> None:
    """Verify that all four required standard manifests exist."""
    required = [
        "manifest_hcmc_d1_peak.json",
        "manifest_hcmc_d5_rain.json",
        "manifest_hanoi_night.json",
        "manifest_synthetic_corridor.json",
    ]
    for filename in required:
        file_path = manifests_dir / filename
        assert file_path.is_file(), f"Missing required manifest {filename}"


def test_all_manifests_pass_validation(manifests_dir: Path) -> None:
    """Ensure all repository manifests pass schema and Decree 13 validation."""
    total, passed, errors = validate_directory(manifests_dir)
    assert total >= 4
    assert passed == total, f"Validation errors encountered: {errors}"
    assert len(errors) == 0


def test_manifest_decree13_enforcement_for_offline_video(manifests_dir: Path) -> None:
    """Assert Decree 13 rules are strictly enforced for physical video captures."""
    hcmc_manifest = manifests_dir / "manifest_hcmc_d1_peak.json"
    with open(hcmc_manifest, encoding="utf-8") as f:
        data = json.load(f)

    # Valid case
    manifest = VideoManifest.model_validate(data)
    assert manifest.validate_decree13_invariants() == []

    # Violation case: face not blurred
    bad_data = json.loads(json.dumps(data))
    bad_data["privacy_compliance"]["face_blurred"] = False
    bad_manifest = VideoManifest.model_validate(bad_data)
    errors = bad_manifest.validate_decree13_invariants()
    assert len(errors) > 0
    assert any("face_blurred" in e for e in errors)

    # Violation case: license plate not blurred
    bad_data2 = json.loads(json.dumps(data))
    bad_data2["privacy_compliance"]["license_plate_blurred"] = False
    bad_manifest2 = VideoManifest.model_validate(bad_data2)
    errors2 = bad_manifest2.validate_decree13_invariants()
    assert len(errors2) > 0
    assert any("license_plate_blurred" in e for e in errors2)


def test_manifest_invalid_sha256_rejected(manifests_dir: Path) -> None:
    """Verify that malformed SHA-256 strings fail Pydantic validation."""
    hcmc_manifest = manifests_dir / "manifest_hcmc_d1_peak.json"
    with open(hcmc_manifest, encoding="utf-8") as f:
        data = json.load(f)

    bad_data = json.loads(json.dumps(data))
    bad_data["integrity"]["sha256_raw"] = "not-a-valid-sha256"

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        VideoManifest.model_validate(bad_data)


def test_validate_single_manifest_file_missing(tmp_path: Path) -> None:
    """Verify validator handles non-existent files gracefully."""
    ok, errors = validate_manifest_file(tmp_path / "non_existent.json")
    assert not ok
    assert len(errors) == 1
    assert "not found" in errors[0]


# =========================================================================
# 3. PRIVACY SCRUBBER & ANONYMIZATION ALGORITHM TESTS
# =========================================================================


def test_bounding_box_operations() -> None:
    """Test bounding box clipping and dimensions."""
    bbox = BoundingBox(x_min=-10, y_min=20, x_max=150, y_max=120)
    clipped = bbox.clip_to_image(100, 100)

    assert clipped.x_min == 0
    assert clipped.y_min == 20
    assert clipped.x_max == 100
    assert clipped.y_max == 100
    assert clipped.width == 100
    assert clipped.height == 80


def test_gaussian_blur_anonymization() -> None:
    """Test Gaussian blur alters the target region while leaving surroundings unchanged."""
    rng = np.random.default_rng(42)
    img = rng.integers(0, 255, size=(100, 100, 3), dtype=np.uint8)

    bbox = (20, 20, 60, 60)
    blurred = apply_gaussian_blur(img, bbox, sigma=4.0)

    # Surrounding outside region must remain identical
    np.testing.assert_array_equal(blurred[:15, :15], img[:15, :15])
    np.testing.assert_array_equal(blurred[75:, 75:], img[75:, 75:])

    # Target region should be smoothed / blurred (not identical to raw noise)
    assert not np.array_equal(blurred[20:60, 20:60], img[20:60, 20:60])
    # The blurred area variance should be lower than original high-frequency noise
    assert np.var(blurred[25:55, 25:55].astype(float)) < np.var(img[25:55, 25:55].astype(float))


def test_pixelation_anonymization() -> None:
    """Test pixelation replaces fine detail with coarse blocks."""
    rng = np.random.default_rng(42)
    img = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)

    bbox = (10, 10, 50, 50)
    pixelated = apply_pixelation(img, bbox, block_size=8)

    # Outside untouched
    np.testing.assert_array_equal(pixelated[:5, :5], img[:5, :5])

    # Inside has flat blocks (uniform values per block)
    block = pixelated[10:18, 10:18, 0]
    assert np.all(block == block[0, 0])


def test_solid_mask_anonymization() -> None:
    """Test solid rectangle blackout redaction."""
    img = np.ones((50, 50, 3), dtype=np.uint8) * 200
    bbox = (10, 10, 30, 30)
    masked = apply_solid_mask(img, bbox, fill_value=0)

    assert np.all(masked[10:30, 10:30] == 0)
    assert np.all(masked[:5, :5] == 200)


def test_privacy_scrubber_frame_pipeline() -> None:
    """Test full multi-target frame redaction pipeline."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    scrubber = PrivacyScrubber(sigma=5.0, plate_block_size=8)

    face_boxes = [(10, 10, 30, 30), (50, 10, 70, 30)]
    plate_boxes = [(20, 60, 40, 75)]

    scrubbed, faces_redacted, plates_redacted = scrubber.scrub_frame(img, face_boxes, plate_boxes)

    assert faces_redacted == 2
    assert plates_redacted == 1
    assert scrubber.version == ANONYMIZER_VERSION
    assert scrubbed.shape == img.shape


def test_sha256_cryptographic_verification(tmp_path: Path) -> None:
    """Test cryptographic SHA-256 chain of custody verification."""
    test_file = tmp_path / "sample_traffic.bin"
    test_file.write_bytes(b"traffic_video_raw_content_123456789")

    digest_file = compute_sha256(test_file)
    digest_bytes = compute_sha256(b"traffic_video_raw_content_123456789")

    assert digest_file == digest_bytes
    assert len(digest_file) == 64

    # Scrubber report verification
    scrubber = PrivacyScrubber()
    report = scrubber.scrub_and_verify(
        raw_bytes=b"sample_frame_buffer_with_faces",
        face_boxes=[(0, 0, 10, 10)],
    )

    assert report.decree_13_compliant is True
    assert report.faces_redacted == 1
    assert report.sha256_raw != report.sha256_anonymized


def test_verify_manifest_decree13_helper(manifests_dir: Path) -> None:
    """Test the verify_manifest_decree13 helper function."""
    with open(manifests_dir / "manifest_hcmc_d1_peak.json", encoding="utf-8") as f:
        data = json.load(f)

    ok, violations = verify_manifest_decree13(data)
    assert ok is True
    assert len(violations) == 0

    # Bad integrity hash
    bad_data = json.loads(json.dumps(data))
    bad_data["integrity"]["sha256_raw"] = "short"
    ok_bad, violations_bad = verify_manifest_decree13(bad_data)
    assert ok_bad is False
    assert any("Integrity error" in v for v in violations_bad)


# =========================================================================
# 4. CLI TOOLS INVOCATION TESTS
# =========================================================================


def test_cli_validate_manifests(manifests_dir: Path) -> None:
    """Test running validate_manifests.py from CLI."""
    import subprocess
    import sys

    # Test directory validation
    res = subprocess.run(
        [
            sys.executable,
            "data/scripts/validate_manifests.py",
            "--manifest-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "SUCCESS" in res.stdout

    # Test single file validation
    single = manifests_dir / "manifest_hcmc_d1_peak.json"
    res_single = subprocess.run(
        [sys.executable, "data/scripts/validate_manifests.py", "--file", str(single)],
        capture_output=True,
        text=True,
    )
    assert res_single.returncode == 0
    assert "[OK]" in res_single.stdout


def test_cli_anonymize(manifests_dir: Path) -> None:
    """Test running anonymize.py from CLI."""
    import subprocess
    import sys

    single = manifests_dir / "manifest_hcmc_d1_peak.json"
    res_check = subprocess.run(
        [sys.executable, "data/scripts/anonymize.py", "--check-manifest", str(single)],
        capture_output=True,
        text=True,
    )
    assert res_check.returncode == 0
    assert "conforms to Decree 13" in res_check.stdout

    res_hash = subprocess.run(
        [sys.executable, "data/scripts/anonymize.py", "--hash", str(single)],
        capture_output=True,
        text=True,
    )
    assert res_hash.returncode == 0
    assert "SHA-256" in res_hash.stdout
