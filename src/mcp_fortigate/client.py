"""Read-only FortiGate REST API client.

This module deliberately exposes only GET operations. There is no path
to a mutation operation through this code.
"""

from __future__ import annotations

from typing import Any

import requests

DEFAULT_TIMEOUT = 30


class FortiGateReadOnly:
    """Strictly read-only FortiGate API client."""

    def __init__(
        self,
        host: str,
        token: str,
        *,
        vdom: str = "root",
        verify_ssl: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = f"https://{host}/api/v2/cmdb"
        self.vdom = vdom
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )
        self.session.verify = verify_ssl

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path}"
        merged_params = {"vdom": self.vdom, **(params or {})}
        response = self.session.get(url, params=merged_params, timeout=self.timeout)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def list_policies(self) -> list[dict[str, Any]]:
        result = self._get("firewall/policy")
        items: list[dict[str, Any]] = result.get("results", [])
        return items

    def get_policy(self, policy_id: int) -> dict[str, Any] | None:
        result = self._get(f"firewall/policy/{policy_id}")
        items: list[dict[str, Any]] = result.get("results", [])
        return items[0] if items else None

    def list_addresses(self) -> list[dict[str, Any]]:
        result = self._get("firewall/address")
        items: list[dict[str, Any]] = result.get("results", [])
        return items

    def list_address_groups(self) -> list[dict[str, Any]]:
        result = self._get("firewall/addrgrp")
        items: list[dict[str, Any]] = result.get("results", [])
        return items

    def close(self) -> None:
        self.session.close()
