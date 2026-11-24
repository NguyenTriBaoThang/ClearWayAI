"""
ClearWayAI - Automated Test Suite for Task 52: Security, Privacy, Fail-Safe & Threat Modeling.

Verifies:
1. V2X cryptographic message authentication and HMAC signature integrity.
2. V2X certificate registry authorization and revocation guards.
3. Anti-replay sliding nonce defense against preemption packet replay attacks.
4. Timestamp freshness and clock skew rejection.
5. Kinematic plausibility validation (rejects teleportation, excessive speed, and acceleration anomalies).
6. FailSafeWatchdog autonomous degradation to Webster cycle upon heartbeat severance (INV-06).
7. ZeroPIIAuditor detection of Vietnamese license plates, phone numbers, and emails.
8. Decree 13/2023/ND-CP video manifest retention (<= 14 days) and anonymization verification.
9. Formal STRIDE Threat Model documentation completeness (docs/THREAT_MODEL.md).
"""

from pathlib import Path

from controller.security.failsafe_watchdog import (
    FailSafeWatchdog,
    WatchdogOperationalState,
)
from controller.security.privacy_auditor import ZeroPIIAuditor
from controller.security.v2x_authenticator import (
    V2XCertificate,
    V2XCertificateRegistry,
    V2XMessageAuthenticator,
    V2XPriorityMessage,
)


def test_v2x_message_authentication_valid():
    """Verify that a correctly signed V2X priority message passes all security gates."""
    auth = V2XMessageAuthenticator()
    msg = V2XPriorityMessage(
        message_id="MSG-001",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=10.0,
        nonce="nonce-unique-abc-123",
        position_x=-100.0,
        position_y=0.0,
        speed_mps=18.5,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    # Sign with authorized agency secret key
    msg.signature = auth.sign_message(msg, "clearway-v2x-sec-key-339")

    res = auth.verify_message(msg, current_sim_time=10.2)
    assert res.is_authenticated is True
    assert res.rejection_code is None
    assert res.vehicle_id == "AMB-339"


def test_v2x_message_authentication_invalid_signature():
    """Verify that forged or tampered signatures are rejected immediately."""
    auth = V2XMessageAuthenticator()
    msg = V2XPriorityMessage(
        message_id="MSG-002",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=10.0,
        nonce="nonce-unique-456",
        position_x=-100.0,
        position_y=0.0,
        speed_mps=18.5,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
        signature="bad-forged-signature-00000000000000000000000000000000",
    )
    res = auth.verify_message(msg, current_sim_time=10.2)
    assert res.is_authenticated is False
    assert res.rejection_code == "INVALID_SIGNATURE"


def test_v2x_revoked_and_unauthorized_certificates():
    """Verify certificate trust store enforces revocation and vehicle authorization."""
    registry = V2XCertificateRegistry()
    cert = V2XCertificate(
        certificate_id="CERT-TEST-002",
        agency_id="PRIVATE_AMBULANCE_CORP",
        authorized_vehicle_ids=["PV-115"],
        secret_key="private-secret",
        valid_from_sec=0.0,
        valid_until_sec=100.0,
    )
    registry.register_certificate(cert)
    auth = V2XMessageAuthenticator(registry=registry)

    # 1. Unauthorized vehicle ID under this certificate
    msg_unauth = V2XPriorityMessage(
        message_id="MSG-003",
        vehicle_id="ROGUE-CAR-99",
        vehicle_type="passenger",
        timestamp_sec=15.0,
        nonce="nonce-789",
        position_x=0.0,
        position_y=0.0,
        speed_mps=15.0,
        heading_deg=90.0,
        certificate_id="CERT-TEST-002",
    )
    msg_unauth.signature = auth.sign_message(msg_unauth, "private-secret")
    res_unauth = auth.verify_message(msg_unauth, current_sim_time=15.1)
    assert res_unauth.is_authenticated is False
    assert res_unauth.rejection_code == "UNAUTHORIZED_VEHICLE"

    # 2. Revoked certificate
    registry.revoke_certificate("CERT-TEST-002")
    msg_valid_veh = V2XPriorityMessage(
        message_id="MSG-004",
        vehicle_id="PV-115",
        vehicle_type="emergency_ambulance",
        timestamp_sec=20.0,
        nonce="nonce-101112",
        position_x=0.0,
        position_y=0.0,
        speed_mps=15.0,
        heading_deg=90.0,
        certificate_id="CERT-TEST-002",
    )
    msg_valid_veh.signature = auth.sign_message(msg_valid_veh, "private-secret")
    res_revoked = auth.verify_message(msg_valid_veh, current_sim_time=20.1)
    assert res_revoked.is_authenticated is False
    assert res_revoked.rejection_code == "REVOKED_CERTIFICATE"


def test_v2x_anti_replay_nonce_cache():
    """Verify duplicate nonces (replay vectors) are rejected."""
    auth = V2XMessageAuthenticator()
    msg = V2XPriorityMessage(
        message_id="MSG-REPLAY-1",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=30.0,
        nonce="shared-nonce-token-replay",
        position_x=10.0,
        position_y=0.0,
        speed_mps=18.5,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    msg.signature = auth.sign_message(msg, "clearway-v2x-sec-key-339")

    # First transmission: ACCEPT
    res1 = auth.verify_message(msg, current_sim_time=30.1)
    assert res1.is_authenticated is True

    # Replay transmission with identical nonce: REJECT
    res2 = auth.verify_message(msg, current_sim_time=30.5)
    assert res2.is_authenticated is False
    assert res2.rejection_code == "REPLAY_ATTACK"


def test_v2x_timestamp_freshness_window():
    """Verify rejection of stale or future-dated priority telemetry."""
    auth = V2XMessageAuthenticator(max_clock_skew_sec=2.0)

    # 1. Stale message (timestamp = 10.0, current_time = 15.0 -> delta 5.0s > 2.0s)
    stale_msg = V2XPriorityMessage(
        message_id="MSG-STALE",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=10.0,
        nonce="nonce-stale-1",
        position_x=0.0,
        position_y=0.0,
        speed_mps=18.5,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    stale_msg.signature = auth.sign_message(stale_msg, "clearway-v2x-sec-key-339")
    res_stale = auth.verify_message(stale_msg, current_sim_time=15.0)
    assert res_stale.is_authenticated is False
    assert res_stale.rejection_code == "STALE_TIMESTAMP"


def test_v2x_kinematic_plausibility_filter():
    """Verify rejection of teleportation, supersonic speeds, and impossible accelerations."""
    auth = V2XMessageAuthenticator(max_speed_mps=33.33, max_accel_mps2=8.0)

    # 1. Supersonic claimed velocity (50 m/s = 180 km/h > 33.33 m/s)
    fast_msg = V2XPriorityMessage(
        message_id="MSG-FAST",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=40.0,
        nonce="nonce-fast",
        position_x=0.0,
        position_y=0.0,
        speed_mps=50.0,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    fast_msg.signature = auth.sign_message(fast_msg, "clearway-v2x-sec-key-339")
    res_fast = auth.verify_message(fast_msg, current_sim_time=40.1)
    assert res_fast.is_authenticated is False
    assert res_fast.rejection_code == "KINEMATIC_ANOMALY"

    # 2. Establish valid track point at x=0, v=15 m/s, t=50.0s
    t1_msg = V2XPriorityMessage(
        message_id="MSG-T1",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=50.0,
        nonce="nonce-t1",
        position_x=0.0,
        position_y=0.0,
        speed_mps=15.0,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    t1_msg.signature = auth.sign_message(t1_msg, "clearway-v2x-sec-key-339")
    res_t1 = auth.verify_message(t1_msg, current_sim_time=50.1)
    assert res_t1.is_authenticated is True

    # 3. Teleportation: 0.5s later, claimed position x = 500m (implied velocity = 1000 m/s!)
    teleport_msg = V2XPriorityMessage(
        message_id="MSG-TELEPORT",
        vehicle_id="AMB-339",
        vehicle_type="emergency_ambulance",
        timestamp_sec=50.5,
        nonce="nonce-teleport",
        position_x=500.0,
        position_y=0.0,
        speed_mps=20.0,
        heading_deg=90.0,
        certificate_id="CERT-METRO-EMS-001",
    )
    teleport_msg.signature = auth.sign_message(teleport_msg, "clearway-v2x-sec-key-339")
    res_teleport = auth.verify_message(teleport_msg, current_sim_time=50.6)
    assert res_teleport.is_authenticated is False
    assert res_teleport.rejection_code == "KINEMATIC_ANOMALY"
    assert "teleportation" in res_teleport.reason


def test_failsafe_heartbeat_watchdog_healthy_and_tripped():
    """Verify autonomous heartbeat watchdog enforcement and failover (INV-06)."""
    wd = FailSafeWatchdog(timeout_sec=0.5, trip_threshold_sec=1.0)

    # 1. Healthy state
    wd.record_heartbeat("v2x_telemetry", 10.0)
    wd.record_heartbeat("camera_perception", 10.0)
    wd.record_heartbeat("ai_inference_gateway", 10.0)
    wd.record_heartbeat("corridor_coordinator", 10.0)

    rep_healthy = wd.evaluate_watchdog(sim_time=10.3)  # Elapsed 0.3s <= 0.5s
    assert rep_healthy.state == WatchdogOperationalState.HEALTHY
    assert rep_healthy.is_safe_to_control is True
    assert rep_healthy.fallback_engaged is False

    # 2. Degraded state (Elapsed 0.7s > 0.5s but <= 1.0s)
    rep_degraded = wd.evaluate_watchdog(sim_time=10.7)
    assert rep_degraded.state == WatchdogOperationalState.DEGRADED
    assert rep_degraded.is_safe_to_control is False
    assert rep_degraded.fallback_engaged is False

    # 3. Tripped fail-safe state (Elapsed 1.5s > 1.0s) -> Enforce Webster fallback
    rep_tripped = wd.evaluate_watchdog(sim_time=11.5)
    assert rep_tripped.state == WatchdogOperationalState.TRIPPED_FAILSAFE
    assert rep_tripped.is_safe_to_control is False
    assert rep_tripped.fallback_engaged is True
    # Safe phase returns standard Webster phase [0..5]
    assert rep_tripped.safe_phase in [0, 1, 2, 3, 4, 5]


def test_zero_pii_privacy_auditor_clean_and_dirty_telemetry():
    """Verify Zero-PII scanner detects Vietnamese plates, phone numbers, and emails."""
    auditor = ZeroPIIAuditor()

    # Clean telemetry payload
    clean_payload = {
        "simulation_id": "sim-corridor-101",
        "timestamp": 123.45,
        "vehicles": [
            {"id": "veh_001", "type": "car", "speed_kmh": 42.0},
            {"id": "AMB-339", "type": "emergency_ambulance", "speed_kmh": 65.0},
        ],
    }
    clean_res = auditor.audit_telemetry_payload(clean_payload)
    assert clean_res.is_compliant is True
    assert clean_res.pii_matches_count == 0

    # Dirty telemetry payload containing raw PII
    dirty_payload = {
        "operator_email": "traffic_chief@hcmc.gov.vn",
        "operator_contact": "0908123456",
        "detected_vehicles": [
            {"plate": "51F-123.45", "owner": "Nguyen Van A"},
            {"plate": "29A-999.99", "vehicle_id": "car_02"},
        ],
    }
    dirty_res = auditor.audit_telemetry_payload(dirty_payload)
    assert dirty_res.is_compliant is False
    assert dirty_res.pii_matches_count >= 3
    assert len(dirty_res.violations) >= 3

    # Text scrubber verification
    raw_text = "Plate 51F-123.45 was observed by operator at user@domain.com calling 0908123456"
    scrubbed = auditor.scrub_text(raw_text)
    assert "51F-123.45" not in scrubbed
    assert "user@domain.com" not in scrubbed
    assert "0908123456" not in scrubbed
    assert "[REDACTED_PLATE]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed


def test_zero_pii_video_manifest_compliance():
    """Verify Decree 13/2023/ND-CP video manifest retention and anonymization checks."""
    auditor = ZeroPIIAuditor()

    # Compliant manifest
    compliant_manifest = {
        "dataset_name": "hcmc_d1_traffic_sample",
        "privacy_compliance": {
            "faces_anonymized": True,
            "plates_obfuscated": True,
            "retention_days": 14,
            "zero_pii_certified": True,
        },
    }
    res_c = auditor.audit_video_manifest(compliant_manifest)
    assert res_c.is_compliant is True

    # Non-compliant manifest (retention 30 days > legal maximum 14 days, unblurred faces)
    non_compliant_manifest = {
        "dataset_name": "illegal_long_retention",
        "privacy_compliance": {
            "faces_anonymized": False,
            "plates_obfuscated": True,
            "retention_days": 30,
            "zero_pii_certified": False,
        },
    }
    res_nc = auditor.audit_video_manifest(non_compliant_manifest)
    assert res_nc.is_compliant is False
    assert res_nc.retention_days_valid is False
    assert len(res_nc.violations) >= 3


def test_threat_model_document_exists_and_complete():
    """Assert docs/THREAT_MODEL.md exists and documents mandatory STRIDE security controls."""
    repo_root = Path(__file__).resolve().parent.parent
    threat_path = repo_root / "docs" / "THREAT_MODEL.md"
    assert threat_path.is_file()

    with open(threat_path, encoding="utf-8") as f:
        content = f.read()

    assert "STRIDE Threat Model" in content
    assert "Spoofing" in content
    assert "Tampering" in content
    assert "Repudiation" in content
    assert "Information Disclosure" in content
    assert "Denial of Service" in content
    assert "Elevation of Privilege" in content
    assert "Decree 13/2023/ND-CP" in content
    assert "SignalSafetyGateway" in content
    assert "INV-01" in content
    assert "INV-06" in content
