# homelab-komodo

GitOps-kilde for Komodo-stacker og driftsdokumentasjon. **Kun de lokale sidene (nettverkskartet og advarselsiden) ligger i Gitea på CT120. Alt annet ligger her.** Se [AGENTS.md](AGENTS.md).

## Drift

- [Komodo stack-deployment runbook](docs/komodo-stack-deployment-runbook.md)
- [Inventar](docs/INVENTORY.md)
- Nettverkskart og advarselsiden (`daily-report.html`): **Gitea/CT120** (`/usr/local/sbin/nettkart-publish`) – finnes **ikke** i GitHub, se [AGENTS.md](AGENTS.md)
- [ntfy-stack](pc6-ct109-ntfy/README.md) — CT109 / 10.0.0.166:2586
- [Hermes AI Matrix-bot](docs/hermes-matrix-ai.md)
- [Hermes tilgangsmatrise](docs/hermes-access.md)

Følg runbookens repo-cache-preflight før PullStack og deploy. Secrets lagres i
Komodo Environment, aldri i Git.

## Periphery-standard for CT-er

Nye CT-er får Komodo Periphery som Docker-container i `/opt/komodo/periphery/`.
Systemd-Periphery i eldre CT-er er ikke feil; de migreres kontrollert senere.
Hver tilgjengelige CT skal ha én Komodo-server med navnet
`<node>-ct<id>-<navn>` og status `Ok`, uten duplikater. Sjekk gjestens
faktiske agent og Proxmox mot Komodo før ny registrering. CT110 (Core) har
Periphery i Core sin Compose. Se [AGENTS.md](AGENTS.md) for kontrollene og
nettverkskartet for verifisert tilstand per CT.
