# Security

## Read-only by design

This MCP server only implements GET HTTP operations against the FortiGate API.
There is no code path through which an LLM agent could mutate firewall state.

## Reporting a vulnerability

Please use [Report a vulnerability](https://github.com/otixe/mcp-fortigate/security/advisories/new) (GitHub Security Advisories).
Do not post tokens, credentials, private configuration or personal data in public issues.
If private reporting is not enabled, request that the maintainer enables it without disclosing vulnerability details.

## What you should NEVER commit

- Real FortiGate API tokens (use placeholders in docs/examples)
- Real firewall hostnames, IPs, policy IDs from production environments
- Real address objects, address groups, or service names

All test fixtures use synthetic data and RFC 5737 documentation IP ranges.
Pre-commit hooks (`detect-secrets`, `detect-private-key`) gate this.

## Recommended IAM/policy on FortiGate side

```
config system api-user
    edit "mcp-readonly"
        set accprofile "audit_readonly"
        set vdom "root"
        set trusthost1 <your-mcp-host>/32
    next
end

config system accprofile
    edit "audit_readonly"
        set system-flags read
        set fwgrp read
        set netgrp read
    next
end
```

The `trusthost1` field is essential — it limits where a compromised token
can be used from.
