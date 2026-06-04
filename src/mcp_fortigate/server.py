"""MCP server exposing read-only FortiGate tools.

Run via stdio: `mcp-fortigate` (after `pip install`).
Configure via environment:
  - FORTIGATE_HOST   : firewall hostname or IP
  - FORTIGATE_TOKEN  : read-only API token
  - FORTIGATE_VDOM   : VDOM name (default: root)
  - FORTIGATE_VERIFY : "false" to skip TLS verification (NOT recommended)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .audit import audit_all, audit_single
from .client import FortiGateReadOnly

server: Server = Server("mcp-fortigate")


def _client_from_env() -> FortiGateReadOnly:
    host = os.environ.get("FORTIGATE_HOST")
    token = os.environ.get("FORTIGATE_TOKEN")
    if not host or not token:
        raise RuntimeError("FORTIGATE_HOST and FORTIGATE_TOKEN environment variables are required")
    return FortiGateReadOnly(
        host=host,
        token=token,
        vdom=os.environ.get("FORTIGATE_VDOM", "root"),
        verify_ssl=os.environ.get("FORTIGATE_VERIFY", "true").lower() != "false",
    )


@server.list_tools()  # type: ignore[no-untyped-call]
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_policies",
            description="List all firewall policies. Returns id, name, action, status, "
            "srcaddr, dstaddr, service for each.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_policy",
            description="Get full details of a single policy by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {"type": "integer", "description": "Policy ID"},
                },
                "required": ["policy_id"],
            },
        ),
        Tool(
            name="list_addresses",
            description="List firewall address objects (hosts, subnets, FQDNs).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_address_groups",
            description="List firewall address groups.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="audit_policy",
            description=(
                "Run direct risk checks against one policy (specify policy_id) "
                "or all enabled policies (omit policy_id). Returns findings with "
                "severity, title, and recommendation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {
                        "type": "integer",
                        "description": "Optional. Audit only this policy.",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    client = _client_from_env()
    try:
        result = _dispatch(client, name, arguments)
    finally:
        client.close()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def _dispatch(client: FortiGateReadOnly, name: str, arguments: dict[str, Any]) -> Any:
    if name == "list_policies":
        policies = client.list_policies()
        return [
            {
                "policyid": p.get("policyid"),
                "name": p.get("name"),
                "action": p.get("action"),
                "status": p.get("status"),
                "srcaddr": [a.get("name") for a in p.get("srcaddr", [])],
                "dstaddr": [a.get("name") for a in p.get("dstaddr", [])],
                "service": [s.get("name") for s in p.get("service", [])],
            }
            for p in policies
        ]
    if name == "get_policy":
        policy = client.get_policy(int(arguments["policy_id"]))
        return policy or {"error": "not found"}
    if name == "list_addresses":
        return client.list_addresses()
    if name == "list_address_groups":
        return client.list_address_groups()
    if name == "audit_policy":
        if "policy_id" in arguments:
            policy = client.get_policy(int(arguments["policy_id"]))
            if not policy:
                return {"error": "policy not found"}
            return {"policy_id": policy.get("policyid"), "findings": audit_single(policy)}
        policies = client.list_policies()
        all_findings = audit_all(policies)
        return {
            "audited": len(policies),
            "policies_with_findings": sum(1 for v in all_findings.values() if v),
            "results": all_findings,
        }
    return {"error": f"unknown tool: {name}"}


def main() -> None:
    """Entry point for the `mcp-fortigate` console script."""
    import asyncio

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
