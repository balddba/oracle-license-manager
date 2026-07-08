"""Shared enumerations for license tracker domain."""

from __future__ import annotations

from enum import StrEnum


class LicenseStatus(StrEnum):
    """License agreement lifecycle status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class LicenseMetric(StrEnum):
    """Oracle license metric types."""

    PROCESSOR = "processor"
    NAMED_USER_PLUS = "named_user_plus"


class CpuProfileSource(StrEnum):
    """How a host CPU profile was collected."""

    MANUAL = "manual"
    SSH_PROBE = "ssh_probe"


class HostEnvironment(StrEnum):
    """Host deployment environment."""

    PRODUCTION = "production"
    NON_PRODUCTION = "non_production"


class HostLicenseType(StrEnum):
    """How a server is licensed (all products on the host share this type)."""

    CPU = "cpu"
    NUP = "nup"
