"""Derived execution-substrate routing for CADS.

This module does not infer risk, grant authority, start a runtime, or persist
workflow state. Design Authority supplies the execution properties that are
material for the current Goal; this module only derives the lightest route class.
"""
from __future__ import annotations

from collections.abc import Iterable


ROUTE_DIRECT = "DIRECT"
ROUTE_GOVERNED = "GOVERNED"

PROPERTY_DESCRIPTIONS: dict[str, str] = {
    "isolated-mutation": "mutation must execute inside an isolation boundary",
    "durable-recovery": "execution must survive/recover from process or host interruption",
    "concurrent-writer-fencing": "multiple or replaceable writers require stale-writer fencing",
    "durable-execution-authority": "execution authority must survive client/session transport loss",
    "resource-governance": "execution needs enforced shared CPU/RAM/disk or worker-capacity governance",
    "crash-safe-integration": "canonical integration/promotion must remain safe across interruption",
}
PROPERTY_ORDER = tuple(PROPERTY_DESCRIPTIONS)


class ExecutionRouteError(ValueError):
    """The caller supplied an invalid execution-substrate requirement."""


def classify(required_properties: Iterable[str]) -> dict[str, object]:
    """Derive DIRECT or GOVERNED from explicit required runtime properties."""

    requested: set[str] = set()
    for raw in required_properties:
        value = str(raw).strip().lower()
        if not value:
            raise ExecutionRouteError("execution property must not be empty")
        if value not in PROPERTY_DESCRIPTIONS:
            raise ExecutionRouteError(f"unknown execution property: {value}")
        requested.add(value)

    ordered = [name for name in PROPERTY_ORDER if name in requested]
    governed = bool(ordered)
    return {
        "result": "PASS",
        "route": ROUTE_GOVERNED if governed else ROUTE_DIRECT,
        "required_properties": ordered,
        "derived_only": True,
        "authority_granted": False,
        "guidance": (
            "select the simplest execution substrate that demonstrably supplies "
            "all declared properties; a durable runtime such as MAR is optional"
            if governed
            else "use the normal direct coding harness path; CADS consequence "
                 "guards and acceptance obligations still apply when relevant"
        ),
    }
