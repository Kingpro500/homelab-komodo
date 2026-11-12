# Tunarr — pc9 CT106 (10.0.0.122:8005)

| | |
|---|---|
| **Komodo-server** | `pc9-ct106-tunarr` (systemd-Periphery, `connect_as` i `/etc/komodo/periphery.config.toml`) |
| **Komodo-stack** | `pc9-ct106-tunarr`, `project_name = tunarr` |

Egen Tunarr-worker, uavhengig av Tunarr på pc6 (CT250). Konfigurasjon i
`/opt/tunarr/config` på verten.

## Mediestiene må bli stående

De seks read-only bindingene under `/media` er NFS fra Tower (10.0.0.101) og er
det Tunarr lager kanaler av. Fram til 12. nov 2026 manglet de i denne filen,
mens de lå i Komodos vertsfil — stacken kjørte altså ikke det som sto i Git.
Blir de borte, mister kanalene filene sine.

Stale NFS overvåkes av stacken `pc9-ct106-nfs-health` i samme CT. Den varsler,
men remounter eller restarter ingenting.

## Hvorfor bildet er festet

`image` står fast på `2026.9.3`. `latest` ødela artwork i 2026.10.3.
