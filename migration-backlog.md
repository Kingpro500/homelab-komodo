# Migration backlog

Every Docker workload is deployed through Komodo; Tower data is retained until
the new service has been accepted.

**Oppdatert 4. oktober 2026.** Den gamle innledelsen sa at arbeidet ventet på
Ollama/n8n/Hermes-arbeidet på pc1. Det er utdatert: Hermes kjører på pc6
(CT157) med OpenRouter som modellleverandør, og Ollama på pc1 har aldri fått
GPU-en. Ingen nåværende oppgave avhenger av pc1-veien.

| Workload | Destination | Status | Notes |
| --- | --- | --- | --- |
| iVentoy | To be chosen | Planned | New dedicated service; identify existing media and network requirements first. |
| UniFi Network Application | Kjører på pc6 CT155 | **Uavklart** | Verifisert 4. okt: CT155 `pc6-ct155-unifi` kjører på `10.0.0.132:8443` (tittel «unifi network»). Men det finnes **ingen Komodo-stack** for den, så den er ikke Komodo-administrert. Tidligere plan sa pc9, egen CT. Avgjør om pc6 beholdes eller flyttes, og legg den under Komodo. |
| Uptime Kuma | pc6 CT 109 | Done | Running through Komodo. Review stale Tower-based monitors separately. |
| Homepage | pc6 CT 109 | Done | Running through Komodo. `services.yaml` er GitOps-mountet read-only fra `homepage/config/`. |
| Speedtest Tracker | pc6 CT 109 | Done | Running through Komodo. |
| Audiobookshelf | pc6 CT 109 | Prepared | Stack files exist locally but are intentionally not deployed or committed yet. |
| Podgrab | pc6 CT 109 | Planned | Identify Tower configuration and storage path before migration. |

## Blockerer utenfor backlogen

- **pc1 / CT156:** valget mellom «løs GPU-en» og «slett CT156» er ikke tatt.
  Se `pc1-ai-roadmap.md`. Løses ikke her.
- **Komodo-alert `pc1-ct156-ollama`:** CRITICAL `ServerUnreachable` siden
  1. oktober 21:50 UTC, fordi Komodo-agenten ikke kjører i CT-en.
- **Komodo-alert `pc6-ct103-node`:** `ServerUnreachable` åpnet 4. oktober 13:59.
  n8n (`.119:5678`) og Open WebUI (`.119:3080`) svarer begge, så CT-en kjører —
  det er agenten som er borte. Samme agent har flappet siden 1. oktober.
- **Homepage GitOps har et hull.** `file_paths` er bare `['docker-compose.yml']`,
  så Komodo henter ikke `services.yaml` fra repoet. Redeploy trekker riktig commit
  (`deployed_hash` matcher), men fila som serveres ligger i repo-klonen på
  verten og er mountet relativt til `run_directory`. Endringene i `services.yaml`
  ble derfor ikke synlige. Se `docs/INVENTORY.md` for detaljer.