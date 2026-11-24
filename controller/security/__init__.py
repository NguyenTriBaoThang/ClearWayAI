"""
ClearWayAI Security, V2X Authentication & Privacy Infrastructure (`controller.security`).

Provides:
- V2XMessageAuthenticator: Cryptographic signature verification, anti-replay nonces, and kinematic plausibility.
- FailSafeWatchdog: Real-time heartbeat monitoring with autonomous failover to Webster cycle.
- ZeroPIIAuditor: Automated compliance audit for Decree 13/2023/ND-CP zero-PII invariants.
"""

from controller.security.failsafe_watchdog import (
    FailSafeWatchdog,
    WatchdogChannelStatus,
    WatchdogOperationalState,
)
from controller.security.privacy_auditor import (
    PrivacyAuditResult,
    ZeroPIIAuditor,
)
from controller.security.v2x_authenticator import (
    KinematicPlausibilityReport,
    V2XAuthenticationResult,
    V2XCertificate,
    V2XCertificateRegistry,
    V2XMessageAuthenticator,
    V2XPriorityMessage,
)

__all__ = [
    "V2XCertificate",
    "V2XCertificateRegistry",
    "V2XPriorityMessage",
    "V2XAuthenticationResult",
    "KinematicPlausibilityReport",
    "V2XMessageAuthenticator",
    "WatchdogOperationalState",
    "WatchdogChannelStatus",
    "FailSafeWatchdog",
    "PrivacyAuditResult",
    "ZeroPIIAuditor",
]
