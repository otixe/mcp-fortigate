"""Tests for the audit module — purely synthetic data."""

from __future__ import annotations

from mcp_fortigate.audit import audit_all, audit_single


def _policy(**overrides) -> dict:
    base = {
        "policyid": 1,
        "name": "test",
        "status": "enable",
        "action": "accept",
        "srcaddr": [{"name": "internal"}],
        "dstaddr": [{"name": "dmz"}],
        "service": [{"name": "HTTPS"}],
        "logtraffic": "all",
    }
    base.update(overrides)
    return base


def test_audit_clean_policy_returns_no_findings() -> None:
    findings = audit_single(_policy())
    assert findings == []


def test_audit_any_to_any_critical() -> None:
    findings = audit_single(
        _policy(
            srcaddr=[{"name": "all"}],
            dstaddr=[{"name": "all"}],
        )
    )
    severities = [f["severity"] for f in findings]
    assert "critical" in severities


def test_audit_service_all_high() -> None:
    findings = audit_single(_policy(service=[{"name": "ALL"}]))
    severities = [f["severity"] for f in findings]
    assert "high" in severities


def test_audit_logging_disabled_medium() -> None:
    findings = audit_single(_policy(logtraffic="disable"))
    severities = [f["severity"] for f in findings]
    assert "medium" in severities


def test_audit_disabled_policy_skipped() -> None:
    assert audit_single(_policy(status="disable")) == []


def test_audit_deny_policy_skipped() -> None:
    assert audit_single(_policy(action="deny")) == []


def test_audit_all_returns_dict_keyed_by_id() -> None:
    policies = [_policy(policyid=1), _policy(policyid=2, service=[{"name": "ALL"}])]
    result = audit_all(policies)
    assert set(result) == {1, 2}
    assert result[1] == []
    assert result[2]
