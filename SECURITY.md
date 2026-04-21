# Security Policy

## Reporting a vulnerability

If you discover a security issue in Workflow Manager, **please do not open a public GitHub issue.**

Instead, email the maintainers privately:

**`tomash.maciag@gmail.com`**

Include:
- A description of the issue
- Steps to reproduce
- The affected version (`skills/wm/VERSION`) if known
- Any suggested mitigation

## Response SLA

- **Acknowledgement:** within 7 days of receipt.
- **Target fix window:** 90 days for confirmed vulnerabilities. Complex issues may take longer; we will keep you updated.

After a fix ships, you are welcome to publish details of the issue. We will credit reporters in the changelog unless asked to omit.

## Scope

**In scope:**
- Workflow Manager commands, skills, workflows, hooks, rules
- The `wm-doc-graph` Python tool
- Install scripts (`install.sh`, `install.ps1`)
- Sanitization tooling (`.gitleaks.toml`, `scripts/sanitize.sh`)

**Out of scope:**
- Claude Code itself — report to Anthropic via their official channels.
- The user's local environment (OS, shell, editor).
- Third-party plugins installed alongside Workflow Manager.
- Bugs that require local filesystem or account access an attacker would not have.

## Disclosure

This policy is public so researchers know how to reach us. The specific mailbox is a private alias; only maintainers read it.
