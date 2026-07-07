"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from license_tracker.api.v1 import catalog, core_factors, health, hosts, license_agreements, reports

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(license_agreements.router)
router.include_router(hosts.router)
router.include_router(core_factors.router)
router.include_router(catalog.router)
router.include_router(reports.router)
