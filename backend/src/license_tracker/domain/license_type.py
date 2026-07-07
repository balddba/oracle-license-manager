"""Map between host license types and entitlement metrics."""

from __future__ import annotations

from license_tracker.domain.enums import HostLicenseType, LicenseMetric

_CPU_METRICS = frozenset(
    {
        LicenseMetric.PROCESSOR,
        LicenseMetric.SOCKET,
        LicenseMetric.OCPU,
    }
)
_NUP_METRICS = frozenset(
    {
        LicenseMetric.NAMED_USER_PLUS,
        LicenseMetric.NAMED_USER,
        LicenseMetric.CONCURRENT_USER,
        LicenseMetric.APPLICATION_USER,
    }
)


def license_type_for_metric(metric: LicenseMetric) -> HostLicenseType | None:
    """Return the host license type for an entitlement metric.

    Args:
        metric (LicenseMetric): Entitlement or assignment metric.

    Returns:
        HostLicenseType | None: CPU or NUP when the metric maps to a host type.
    """
    if metric in _CPU_METRICS:
        return HostLicenseType.CPU
    if metric in _NUP_METRICS:
        return HostLicenseType.NUP
    return None


def metric_for_license_type(license_type: HostLicenseType) -> LicenseMetric:
    """Return the stored metric for a host license type.

    Args:
        license_type (HostLicenseType): CPU or NUP.

    Returns:
        LicenseMetric: Processor for CPU, Named User Plus for NUP.
    """
    if license_type == HostLicenseType.CPU:
        return LicenseMetric.PROCESSOR
    return LicenseMetric.NAMED_USER_PLUS


def metrics_for_license_type(license_type: HostLicenseType) -> frozenset[LicenseMetric]:
    """Return entitlement metrics that count toward a host license type.

    Args:
        license_type (HostLicenseType): CPU or NUP.

    Returns:
        frozenset[LicenseMetric]: Metrics included in the pool for that type.
    """
    if license_type == HostLicenseType.CPU:
        return _CPU_METRICS
    return _NUP_METRICS
