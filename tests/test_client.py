"""Tests for the FortiGate client using `responses` library to mock HTTP."""

from __future__ import annotations

import pytest
import responses

from mcp_fortigate.client import FortiGateReadOnly


@pytest.fixture
def client() -> FortiGateReadOnly:
    return FortiGateReadOnly(host="example.test", token="readonly-token", verify_ssl=False)


@responses.activate
def test_list_policies(client: FortiGateReadOnly) -> None:
    responses.add(
        method=responses.GET,
        url="https://example.test/api/v2/cmdb/firewall/policy",
        json={"results": [{"policyid": 1, "name": "test"}]},
        status=200,
    )
    result = client.list_policies()
    assert result == [{"policyid": 1, "name": "test"}]


@responses.activate
def test_get_policy(client: FortiGateReadOnly) -> None:
    responses.add(
        method=responses.GET,
        url="https://example.test/api/v2/cmdb/firewall/policy/42",
        json={"results": [{"policyid": 42, "name": "found"}]},
        status=200,
    )
    result = client.get_policy(42)
    assert result == {"policyid": 42, "name": "found"}


@responses.activate
def test_get_policy_not_found(client: FortiGateReadOnly) -> None:
    responses.add(
        method=responses.GET,
        url="https://example.test/api/v2/cmdb/firewall/policy/999",
        json={"results": []},
        status=200,
    )
    assert client.get_policy(999) is None


@responses.activate
def test_list_addresses(client: FortiGateReadOnly) -> None:
    responses.add(
        method=responses.GET,
        url="https://example.test/api/v2/cmdb/firewall/address",
        json={"results": [{"name": "internal-net", "type": "ipmask", "subnet": "198.18.0.0/15"}]},
        status=200,
    )
    result = client.list_addresses()
    assert result[0]["name"] == "internal-net"
