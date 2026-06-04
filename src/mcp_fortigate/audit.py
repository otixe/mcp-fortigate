"""Audit checks (subset of fortigate-policy-auditor, kept self-contained)."""

from __future__ import annotations

import ipaddress
from typing import Any

CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"


def _service_names(policy: dict[str, Any]) -> list[str]:
    services = policy.get("service", [])
    if isinstance(services, list):
        return [s["name"] if isinstance(s, dict) else str(s) for s in services]
    return []


def _addr_names(policy: dict[str, Any], field: str) -> list[str]:
    items = policy.get(field, [])
    if isinstance(items, list):
        return [a["name"] if isinstance(a, dict) else str(a) for a in items]
    return []


def _is_any_service(policy: dict[str, Any]) -> bool:
    return any(s.upper() in {"ALL", "ANY"} for s in _service_names(policy))


def _broad_subnet(addr: dict[str, Any]) -> bool:
    if addr.get("type") != "ipmask":
        return False
    subnet = addr.get("subnet")
    if not subnet:
        return False
    try:
        net = ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return False
    return net.prefixlen <= 16


def audit_single(policy: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of {severity, title, recommendation} findings for one policy."""
    findings: list[dict[str, str]] = []

    if policy.get("status") != "enable" or policy.get("action") != "accept":
        return findings

    src_any = "all" in {a.lower() for a in _addr_names(policy, "srcaddr")}
    dst_any = "all" in {a.lower() for a in _addr_names(policy, "dstaddr")}

    if src_any and dst_any:
        findings.append(
            {
                "severity": CRITICAL,
                "title": "any→any accept policy",
                "recommendation": (
                    "Replace 'all' with explicit address objects on at least one side."
                ),
            }
        )

    if _is_any_service(policy):
        findings.append(
            {
                "severity": HIGH,
                "title": "service ALL — any future CVE in any service is exposed",
                "recommendation": "Restrict to named services only.",
            }
        )

    if policy.get("logtraffic") == "disable":
        findings.append(
            {
                "severity": MEDIUM,
                "title": "logging disabled on accept policy",
                "recommendation": "Enable logtraffic=all for audit trail.",
            }
        )

    return findings


def audit_all(policies: list[dict[str, Any]]) -> dict[int, list[dict[str, str]]]:
    return {p["policyid"]: audit_single(p) for p in policies if p.get("policyid")}
