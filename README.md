# homelab-komodo

GitOps-kilde for Komodo-stacker og driftsdokumentasjon. **Nettverkskartet ligger i Gitea på CT120, ikke her** – se [AGENTS.md](AGENTS.md).

## Drift

- [Komodo stack-deployment runbook](docs/komodo-stack-deployment-runbook.md)
- [Inventar](docs/INVENTORY.md)
- Nettverkskart: **Gitea/CT120** (`/usr/local/sbin/nettkart-publish`) – finnes **ikke** i GitHub, se [AGENTS.md](AGENTS.md)
- [ntfy-stack](pc6-ct109-ntfy/README.md) — CT109 / 10.0.0.166:2586
- [Hermes AI Matrix-bot](docs/hermes-matrix-ai.md)

Følg runbookens repo-cache-preflight før PullStack og deploy. Secrets lagres i
Komodo Environment, aldri i Git.
