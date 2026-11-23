"""
ClearWayAI - V2X Message Authentication & Anti-Spoofing Engine (`controller.security.v2x_authenticator`).

Provides defense-in-depth protection for priority preemption requests:
1. Cryptographic Authentication (IEEE 1609.2-inspired PKI verification & HMAC signatures)
2. Freshness & Clock Skew Guard (rejection of stale or future-dated telemetry)
3. Anti-Replay Nonce Sliding Cache (detection and rejection of duplicate replay vectors)
4. Kinematic Plausibility Validator (detection of phantom emergency vehicle injection,
   unnatural acceleration jumps > 8 m/s^2, teleportation, or supersonic speeds)
"""

from __future__ import annotations

import hashlib
import hmac
import math
from dataclasses import dataclass


@dataclass
class V2XCertificate:
    """Public digital certificate for an authorized emergency response agency."""

    certificate_id: str
    agency_id: str
    authorized_vehicle_ids: list[str]
    secret_key: str  # In production, ECDSA private key; in simulation, shared secret
    valid_from_sec: float
    valid_until_sec: float
    is_revoked: bool = False

    def is_valid_at(self, current_time: float) -> bool:
        """Check if certificate is active and not expired or revoked."""
        if self.is_revoked:
            return False
        return self.valid_from_sec <= current_time <= self.valid_until_sec


class V2XCertificateRegistry:
    """Manages trusted root and intermediate V2X agency certificates."""

    def __init__(self) -> None:
        self._certificates: dict[str, V2XCertificate] = {}

    def register_certificate(self, cert: V2XCertificate) -> None:
        self._certificates[cert.certificate_id] = cert

    def revoke_certificate(self, certificate_id: str) -> bool:
        if certificate_id in self._certificates:
            self._certificates[certificate_id].is_revoked = True
            return True
        return False

    def get_certificate(self, certificate_id: str) -> V2XCertificate | None:
        return self._certificates.get(certificate_id)


@dataclass
class V2XPriorityMessage:
    """Typed priority pre-clearance beacon message broadcast by emergency vehicle."""

    message_id: str
    vehicle_id: str
    vehicle_type: str
    timestamp_sec: float
    nonce: str
    position_x: float
    position_y: float
    speed_mps: float
    heading_deg: float
    certificate_id: str
    signature: str = ""

    def payload_string(self) -> str:
        """Canonical string serialization for cryptographic signing."""
        return (
            f"{self.message_id}:{self.vehicle_id}:{self.vehicle_type}:"
            f"{self.timestamp_sec:.2f}:{self.nonce}:{self.position_x:.2f}:"
            f"{self.position_y:.2f}:{self.speed_mps:.2f}:{self.heading_deg:.1f}:"
            f"{self.certificate_id}"
        )


@dataclass
class KinematicPlausibilityReport:
    """Result of vehicle kinematic physics verification."""

    is_plausible: bool
    reason: str
    implied_speed_mps: float = 0.0
    implied_accel_mps2: float = 0.0


@dataclass
class V2XAuthenticationResult:
    """Standard audit response for a received V2X priority preemption message."""

    is_authenticated: bool
    rejection_code: str | None
    reason: str
    message_id: str
    vehicle_id: str
    timestamp_sec: float
    kinematic_report: KinematicPlausibilityReport | None = None
    provenance: str = "V2X_SECURITY_GATEWAY"


class V2XMessageAuthenticator:
    """
    Independent V2X message authentication gateway.
    Verifies cryptographic integrity, anti-replay freshness, and physical kinematics.
    """

    def __init__(
        self,
        registry: V2XCertificateRegistry | None = None,
        max_clock_skew_sec: float = 2.0,
        max_speed_mps: float = 33.33,  # 120 km/h emergency ceiling
        max_accel_mps2: float = 8.0,  # 8 m/s^2 maximum physical emergency deceleration/acceleration
        nonce_cache_ttl_sec: float = 60.0,
    ) -> None:
        self.registry = registry or V2XCertificateRegistry()
        self.max_clock_skew_sec = max_clock_skew_sec
        self.max_speed_mps = max_speed_mps
        self.max_accel_mps2 = max_accel_mps2
        self.nonce_cache_ttl_sec = nonce_cache_ttl_sec

        # Nonce sliding cache: nonce -> ingestion_timestamp
        self._seen_nonces: dict[str, float] = {}
        # Track history: vehicle_id -> (last_timestamp, last_x, last_y, last_speed)
        self._kinematic_tracks: dict[str, tuple[float, float, float, float]] = {}

        # Default certificate for standard fleet (e.g. Metropolitan Trauma Center AMB-339)
        self._init_default_certificates()

    def _init_default_certificates(self) -> None:
        """Register default agency certificates for simulated emergency fleets."""
        default_cert = V2XCertificate(
            certificate_id="CERT-METRO-EMS-001",
            agency_id="METROPOLITAN_EMERGENCY_SERVICES",
            authorized_vehicle_ids=["AMB-339", "AMB-101", "FIRE-01"],
            secret_key="clearway-v2x-sec-key-339",
            valid_from_sec=0.0,
            valid_until_sec=1e9,
        )
        self.registry.register_certificate(default_cert)

    @staticmethod
    def sign_message(message: V2XPriorityMessage, secret_key: str) -> str:
        """Generate SHA-256 HMAC cryptographic signature for message payload."""
        payload = message.payload_string().encode("utf-8")
        key_bytes = secret_key.encode("utf-8")
        return hmac.new(key_bytes, payload, hashlib.sha256).hexdigest()

    def _purge_expired_nonces(self, current_time: float) -> None:
        """Purge nonces that have exceeded sliding cache time-to-live."""
        expired = [
            n
            for n, ts in self._seen_nonces.items()
            if (current_time - ts) > self.nonce_cache_ttl_sec
        ]
        for n in expired:
            del self._seen_nonces[n]

    def check_kinematic_plausibility(
        self,
        message: V2XPriorityMessage,
    ) -> KinematicPlausibilityReport:
        """
        Verify physical plausibility of claimed vehicle motion:
        - Absolute speed <= max_speed_mps
        - Implied speed between consecutive timestamps <= max_speed_mps
        - Implied acceleration between consecutive timestamps <= max_accel_mps2
        """
        # 1. Absolute velocity ceiling check
        if message.speed_mps > self.max_speed_mps or message.speed_mps < 0.0:
            return KinematicPlausibilityReport(
                is_plausible=False,
                reason=f"Claimed speed {message.speed_mps:.1f} m/s exceeds physical limit {self.max_speed_mps:.1f} m/s",
                implied_speed_mps=message.speed_mps,
            )

        # 2. Check track history
        if message.vehicle_id in self._kinematic_tracks:
            last_t, last_x, last_y, last_v = self._kinematic_tracks[message.vehicle_id]
            dt = message.timestamp_sec - last_t
            if dt <= 0.001:
                # Disallow zero or negative time intervals with different data
                return KinematicPlausibilityReport(
                    is_plausible=False,
                    reason=f"Non-positive delta time dt={dt:.3f}s from previous track point",
                )

            dx = message.position_x - last_x
            dy = message.position_y - last_y
            dist = math.sqrt(dx * dx + dy * dy)
            implied_v = dist / dt
            dv = abs(message.speed_mps - last_v)
            implied_a = dv / dt

            # Teleportation check: vehicle cannot travel faster than max_speed + buffer
            if implied_v > (self.max_speed_mps * 1.25):
                return KinematicPlausibilityReport(
                    is_plausible=False,
                    reason=f"Implied velocity {implied_v:.1f} m/s indicates phantom teleportation anomaly",
                    implied_speed_mps=round(implied_v, 2),
                    implied_accel_mps2=round(implied_a, 2),
                )

            # Acceleration jump check
            if implied_a > self.max_accel_mps2:
                return KinematicPlausibilityReport(
                    is_plausible=False,
                    reason=f"Implied acceleration {implied_a:.1f} m/s^2 exceeds physical traction limit {self.max_accel_mps2:.1f} m/s^2",
                    implied_speed_mps=round(implied_v, 2),
                    implied_accel_mps2=round(implied_a, 2),
                )

        # Update track state
        self._kinematic_tracks[message.vehicle_id] = (
            message.timestamp_sec,
            message.position_x,
            message.position_y,
            message.speed_mps,
        )
        return KinematicPlausibilityReport(
            is_plausible=True,
            reason="Kinematic trajectory conforms to physical emergency vehicle dynamics.",
            implied_speed_mps=message.speed_mps,
        )

    def verify_message(
        self,
        message: V2XPriorityMessage,
        current_sim_time: float,
    ) -> V2XAuthenticationResult:
        """
        Verify incoming priority message through multi-stage security pipeline:
        Stage 1: Certificate validity & vehicle authorization
        Stage 2: Cryptographic signature verification
        Stage 3: Timestamp freshness & clock skew
        Stage 4: Anti-replay sliding nonce check
        Stage 5: Kinematic plausibility filter
        """
        self._purge_expired_nonces(current_sim_time)

        # Stage 1: Certificate Check
        cert = self.registry.get_certificate(message.certificate_id)
        if cert is None:
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code="UNKNOWN_CERTIFICATE",
                reason=f"Certificate '{message.certificate_id}' not found in V2X trust store.",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )

        if not cert.is_valid_at(current_sim_time):
            code = "REVOKED_CERTIFICATE" if cert.is_revoked else "EXPIRED_CERTIFICATE"
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code=code,
                reason=f"Certificate '{message.certificate_id}' is invalid (revoked={cert.is_revoked}).",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )

        if message.vehicle_id not in cert.authorized_vehicle_ids:
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code="UNAUTHORIZED_VEHICLE",
                reason=f"Vehicle '{message.vehicle_id}' not authorized under agency certificate.",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )

        # Stage 2: Cryptographic Signature Verification
        expected_sig = self.sign_message(message, cert.secret_key)
        if not hmac.compare_digest(expected_sig, message.signature):
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code="INVALID_SIGNATURE",
                reason="HMAC cryptographic signature mismatch (tampering or spoofing detected).",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )

        # Stage 3: Timestamp Freshness & Clock Skew
        clock_delta = abs(current_sim_time - message.timestamp_sec)
        if clock_delta > self.max_clock_skew_sec:
            code = (
                "STALE_TIMESTAMP"
                if message.timestamp_sec < current_sim_time
                else "FUTURE_TIMESTAMP"
            )
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code=code,
                reason=f"Timestamp clock delta {clock_delta:.2f}s exceeds freshness window {self.max_clock_skew_sec:.1f}s.",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )

        # Stage 4: Anti-Replay Nonce Check
        if message.nonce in self._seen_nonces:
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code="REPLAY_ATTACK",
                reason=f"Duplicate nonce '{message.nonce}' detected in sliding cache (replay vector).",
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
            )
        self._seen_nonces[message.nonce] = current_sim_time

        # Stage 5: Kinematic Plausibility Check
        kin_report = self.check_kinematic_plausibility(message)
        if not kin_report.is_plausible:
            return V2XAuthenticationResult(
                is_authenticated=False,
                rejection_code="KINEMATIC_ANOMALY",
                reason=kin_report.reason,
                message_id=message.message_id,
                vehicle_id=message.vehicle_id,
                timestamp_sec=current_sim_time,
                kinematic_report=kin_report,
            )

        return V2XAuthenticationResult(
            is_authenticated=True,
            rejection_code=None,
            reason="V2X priority message successfully authenticated across all 5 security gates.",
            message_id=message.message_id,
            vehicle_id=message.vehicle_id,
            timestamp_sec=current_sim_time,
            kinematic_report=kin_report,
        )
