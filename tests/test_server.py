"""Offline SDK/stdio and missing-config contracts; no real FortiGate access."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_fortigate import server as module


def test_server_lists_read_only_tools() -> None:
    tools = asyncio.run(module.list_tools())
    assert {tool.name for tool in tools} == {
        "list_policies",
        "get_policy",
        "list_addresses",
        "list_address_groups",
        "audit_policy",
    }
    assert all(tool.inputSchema["type"] == "object" for tool in tools)


def test_missing_configuration_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORTIGATE_HOST", raising=False)
    monkeypatch.delenv("FORTIGATE_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="environment variables are required"):
        module._client_from_env()


def test_client_preserves_tls_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORTIGATE_HOST", "example.test")
    monkeypatch.setenv("FORTIGATE_TOKEN", "fixture-only-not-a-real-token")
    monkeypatch.delenv("FORTIGATE_VERIFY", raising=False)
    client = module._client_from_env()
    try:
        assert client.session.verify is True
    finally:
        client.close()


def test_call_closes_client_on_dispatch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    monkeypatch.setattr(module, "_client_from_env", lambda: client)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("fixture dispatch failure")

    monkeypatch.setattr(module, "_dispatch", fail)
    with pytest.raises(RuntimeError, match="fixture dispatch failure"):
        asyncio.run(module.call_tool("list_policies", {}))
    client.close.assert_called_once()


def test_fresh_stdio_initialize_list_and_missing_config_error() -> None:
    async def probe() -> None:
        # Explicit environment: no inherited credentials or user AWS/backend config.
        env = {key: os.environ[key] for key in ("PATH", "HOME", "PYTHONPATH") if key in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_fortigate.server"],
            env=env,
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "mcp-fortigate"
            tools = await session.list_tools()
            assert len(tools.tools) == 5
            result = await session.call_tool("list_policies", {})
            assert result.isError is True
            assert any(
                "environment variables are required" in item.text
                for item in result.content
                if hasattr(item, "text")
            )

    asyncio.run(asyncio.wait_for(probe(), timeout=15))
