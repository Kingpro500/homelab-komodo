# n8n on pc8 CT310

- **Host:** pc8 (`10.0.0.102`)
- **LXC:** CT310 (`pc8-ct310-n8n`)
- **IP:** `10.0.0.119`
- **URL:** `http://10.0.0.119:5678`
- **Komodo-server:** `pc8-ct310-n8n` (ID `6abdec74478bbf9f98ef3ca3`); systemd-Periphery i gjesten.
- **Stack:** `pc6-ct103-n8n` (ID `6abdecb1478bbf9f98ef3cdc`), peker på serveren over og bruker denne historiske repository-stien. Den kjørende Compose-containeren har også et eldre prosjektmerke `pc1-ct103-n8n`. Ikke flytt/endre stacksti eller prosjektnavn bare for kosmetikk: dette kan gjenskape n8n og avbryte automasjonene. Verifiser eierskap og data før en kontrollert migrering.
- **Inventaravvik:** NetBox VM ID 20 har fortsatt navn `pc6-ct310-n8n`; NetBox-credentialen i n8n kan opprette/lese VM-er, men PATCH av eksisterende objekt svarte 403. Endring i NetBox krever en identitet med VM change-tilgang.

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

CT310 kjører nå på pc8; repository-katalogen og stacknavnet beholder historiske
pc6/CT103-navn inntil en separat, kontrollert migrering. Den kjørende
instansen på pc8 er uavhengig av pc1s Windows-oppstarter.

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
| Homelab – daglig helsestatus (**deaktivert historikk**) – se [legacy credential-status](docs/gjeld-paperless-legacy.md) | daglig 20:00 | [docs/homelab-daglig-helsestatus.md](docs/homelab-daglig-helsestatus.md) | [workflows/homelab-daglig-helsestatus.json](workflows/homelab-daglig-helsestatus.json) |
| Nettverksovervaakning | time + daglig 08:00 | [docs/nettverksovervaakning.md](docs/nettverksovervaakning.md) | [workflows/nettverksovervaakning.json](workflows/nettverksovervaakning.json) |
| Pi-hole DNS failover | hvert minutt | [docs/pihole-dns-failover.md](docs/pihole-dns-failover.md) | [workflows/pihole-dns-failover.json](workflows/pihole-dns-failover.json) |
| Media health – deep probes and guarded recovery | hvert 5. min; NFS + Emby-fil + begge Tunarr-videosegmenter | [docs/tower-media-nfs-health-repair.md](docs/tower-media-nfs-health-repair.md) | [workflows/tower-media-nfs-health-repair.json](workflows/tower-media-nfs-health-repair.json) |
| WAN offentlig IP-vakt | hvert 6. time | [docs/wan-offentlig-ip-vakt.md](docs/wan-offentlig-ip-vakt.md) | [workflows/wan-offentlig-ip-vakt.json](workflows/wan-offentlig-ip-vakt.json) |
| Lagring - full-fremskrivning | daglig 08:30 | [docs/lagring-full-fremskrivning.md](docs/lagring-full-fremskrivning.md) | [workflows/lagring-full-fremskrivning.json](workflows/lagring-full-fremskrivning.json) |
| Homelab-ressurs-alarmer (webhook `homelab-alerts`) | webhook | [docs/homelab-alerts.md](docs/homelab-alerts.md) | [workflows/homelab-alerts.json](workflows/homelab-alerts.json) |
| NetBox – opprett nye Proxmox-CT-er | hver time | [docs/netbox-proxmox-ct-inventory.md](docs/netbox-proxmox-ct-inventory.md) | [workflows/netbox-proxmox-ct-inventory.json](workflows/netbox-proxmox-ct-inventory.json) |
| CT-opprettelse: kart og SmokePing gapvarsel | hver time + webhook; deduplisert varsel for nye CT-er | [docs/ct-monitor-gap.md](docs/ct-monitor-gap.md) | [workflows/ct-monitor-gap.json](workflows/ct-monitor-gap.json) |
| Emby - overvaaking og autorestart (**deaktivert, supersedert av Media health**) | ingen; beholdt som historikk | [docs/emby-overvaaking-autorestart.md](docs/emby-overvaaking-autorestart.md) | [workflows/emby-overvaaking-autorestart.json](workflows/emby-overvaaking-autorestart.json) |
| Media playback performance watch (**read-only**) | hvert 2. minutt; transcode-speed, buffer og deduplisert varsel | [docs/media-playback-performance-watch.md](docs/media-playback-performance-watch.md) | [workflows/media-playback-performance-watch.json](workflows/media-playback-performance-watch.json) |
| CT reconcile orchestrator (generisk VMID) | webhook `/ct-reconcile` | [docs/ct-reconcile-orchestrator.md](docs/ct-reconcile-orchestrator.md) | [workflows/ct-reconcile-orchestrator.json](workflows/ct-reconcile-orchestrator.json) |
| Homelab-ressurs-alarmer | Alertmanager webhook | [docs/homelab-ressurs-alarmer.md](docs/homelab-ressurs-alarmer.md) | [workflows/homelab-ressurs-alarmer.json](workflows/homelab-ressurs-alarmer.json) |
| Hendelseslogg - FerretDB | webhook `/events` | [docs/hendelseslogg-ferretdb.md](docs/hendelseslogg-ferretdb.md) | [workflows/hendelseslogg-ferretdb.json](workflows/hendelseslogg-ferretdb.json) |
| AI-modus – frigjør PC1 | webhook `/ai-start` + `/ai-stop` | [docs/ai-modus-frigjor-pc1.md](docs/ai-modus-frigjor-pc1.md) | [workflows/ai-modus-frigjor-pc1.json](workflows/ai-modus-frigjor-pc1.json) |
| PC1 GPU-vakt | Prometheus/Alertmanager webhook | [docs/pc1-gpu-vakt.md](docs/pc1-gpu-vakt.md) | [workflows/pc1-gpu-vakt.json](workflows/pc1-gpu-vakt.json) |
| PC1 AI-heng-vakt | hvert minutt; tre mislykkede Ollama-sjekker | [docs/pc1-ai-heng-vakt.md](docs/pc1-ai-heng-vakt.md) | [workflows/pc1-ai-heng-vakt.json](workflows/pc1-ai-heng-vakt.json) |
| PC1 full heng – varsel | hvert minutt; fem uavhengige feilrunder | [docs/pc1-full-heng-varsel.md](docs/pc1-full-heng-varsel.md) | [workflows/pc1-full-heng-varsel.json](workflows/pc1-full-heng-varsel.json) |
| Komodo-versjonsvakt | daglig 05:15 + webhook | [docs/komodo-versjonsvakt.md](docs/komodo-versjonsvakt.md) | [workflows/komodo-versjonsvakt.json](workflows/komodo-versjonsvakt.json) |
| Nettverkskart-vakt | daglig 08:30 | [docs/nettverkskart-vakt.md](docs/nettverkskart-vakt.md) | [workflows/nettverkskart-vakt.json](workflows/nettverkskart-vakt.json) |
| Podgrab minnevakt | hvert 10. minutt | [docs/podgrab-minnevakt.md](docs/podgrab-minnevakt.md) | [workflows/podgrab-minnevakt.json](workflows/podgrab-minnevakt.json) |

Driftsprinsipper for hvordan n8n-automasjoner bygges, sikres og gjenopprettes
er samlet i [docs/operations/n8n-workflows.md](../docs/operations/n8n-workflows.md).

| AI-modus – Ollama PC1 | `ai-modus---frigjor-pc1.json` | Aktiv start/stopp av CT350 med Ollama-health ved start |
