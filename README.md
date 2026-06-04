# mcp-fortigate

<div align="center">

🔌 **MCP server for FortiGate firewalls**

*Let Claude (and other MCP-compatible agents) audit your firewall — safely, read-only*

[![CI](https://github.com/otixe/mcp-fortigate/actions/workflows/ci.yml/badge.svg)](https://github.com/otixe/mcp-fortigate/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-1.0-7c3aed.svg)](https://modelcontextprotocol.io)

</div>

---

## What is this?

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
FortiGate firewall data to LLM agents over stdio.

Connect it to Claude Desktop, Cursor, or any MCP client — your agent can now:

- 🔍 Inspect firewall policies, address objects, address groups, and services
- 🕸️ Detect risky umbrella rules and overly broad sources
- 📊 Generate audit reports on demand
- 🛡️ **Read-only by design** — agent literally cannot modify your firewall

The complement to [`fortigate-policy-auditor`](https://github.com/otixe/fortigate-policy-auditor):
that runs as a CLI/CI tool, this one lets a conversational agent drive the audit.

---

## Tools exposed

| Tool | Purpose |
|------|---------|
| `list_policies` | List firewall policies with filters (interface, action, status) |
| `get_policy` | Fetch a single policy with full details |
| `list_addresses` | Enumerate address objects |
| `list_address_groups` | Enumerate address groups |
| `audit_policy` | Run direct + indirect risk checks against one or all policies |

All tools are **read-only**. No `set`, no `edit`, no `delete` operations are
exposed under any circumstance.

---

## Install

```bash
pip install mcp-fortigate
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "fortigate": {
      "command": "mcp-fortigate",
      "env": {
        "FORTIGATE_HOST": "firewall.example.com",
        "FORTIGATE_TOKEN": "your-readonly-token",
        "FORTIGATE_VDOM": "root"
      }
    }
  }
}
```

Restart Claude Desktop. Your agent now has firewall-aware tools.

## Use with any MCP client

```bash
export FORTIGATE_HOST=firewall.example.com
export FORTIGATE_TOKEN=your-readonly-token
mcp-fortigate  # listens on stdio
```

---

## Example prompt

> "Audit the firewall for any policies that grant `ALL` services from broad
> internal subnets. For each finding, suggest a least-privilege replacement."

The agent will call `list_policies`, then `audit_policy` on suspicious ones,
then return a curated report with concrete recommendations.

---

## Security

This server is **read-only** by construction. The underlying API client only
implements `GET` operations. There is no code path that produces a mutation.

For the FortiGate side:

```
config system api-user
    edit "mcp-readonly"
        set accprofile "audit_readonly"
        set vdom "root"
        set trusthost1 <host-running-mcp-server>/32
    next
end
```

See [`SECURITY.md`](SECURITY.md) for the full threat model and IAM recommendations.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [@otixe](https://github.com/otixe) — DevOps & Agentic Systems Engineer · 🇨🇱
