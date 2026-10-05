# n8n on pc6 CT 103

- **Host:** pc6 (`10.0.0.120`)
- **LXC:** `pc6-ct103-node`
- **IP:** `10.0.0.119`
- **URL:** `http://10.0.0.119:5678`

The stack uses a dedicated PostgreSQL 16 database. Its application state and
database are stored only in `/opt/n8n` inside the LXC; values for the database
password and n8n encryption key are Komodo secret variables and never belong
in Git.

## Why it moved off pc1

CT 103 was originally on pc1 and shared the host with Ollama in CT 156. pc1 is
dual boot: it runs Windows for gaming several times a day, and every reboot took
n8n and all its automations offline with it. Local LLM inference on pc1 also
proved unusable for agent work (CPU-only, ~9 s per short reply), so the workload
split was not worth the dependency.

CT 103 now lives on pc6, a host that is always on. n8n no longer disappears when
Windows boots.

Ollama stays in CT 156 on pc1 with autostart disabled until GPU access is fixed.
It is independent of n8n and no longer needs to be started or stopped around it.

## Workflows

Versioned workflow definitions belong in `workflows/`; operational principles,
secret-handling rules and recovery notes live in
[docs/operations/n8n-workflows.md](../docs/operations/n8n-workflows.md). The
exported JSON never contains secrets — `X-Audit-Token` and the Home Assistant
token are placeholders (`REDACTED_*`) that must be restored from n8n
credentials/Secrets at import time (see each doc's "Gjenoppretting"). n8n
credentials, Home Assistant tokens and SSH private keys remain only in the
running service.

| Workflow | Trigger | Doc | Eksport |
|---|---|---|---|
| Daglig homelab-diagnose | daglig 08:15 | [docs/daglig-homelab-diagnose.md](docs/daglig-homelab-diagnose.md) | [workflows/daglig-homelab-diagnose.json](workflows/daglig-homelab-diagnose.json) |
| Nettverksovervaakning | time + daglig 08:00 | [docs/nettverksovervaakning.md](docs/nettverksovervaakning.md) | [workflows/nettverksovervaakning.json](workflows/nettverksovervaakning.json) |
| Tower media NFS health and repair | hvert 5. min | _ikke dokumentert ennå_ | [workflows/tower-media-nfs-health-repair.json](workflows/tower-media-nfs-health-repair.json) |
