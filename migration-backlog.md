# Migration backlog

Every Docker workload is deployed through Komodo; Tower data is retained until
the new service has been accepted.

**Oppdatert 4. oktober 2026.** Den gamle innledelsen sa at arbeidet ventet på
Ollama/n8n/Hermes-arbeidet på pc1. Det er utdatert: Hermes kjører på pc6
(CT157) med OpenRouter som modellleverandør, og Ollama på pc1 har aldri fått
GPU-en. Ingen nåværende oppgave avhenger av pc1-veien.

| Workload | Destination | Status | Notes |
| --- | --- | --- | --- |
| iVentoy | pc9 CT111 | Done | Moved from pc6 6. okt 2026. Runs Komodo-managed at 10.0.0.134:26000. |
| UniFi Network Application | pc9 CT155 | **Done (moved 6. okt)** | CT155 `pc6-ct155-unifi` moved from pc6 to pc9; runs at 10.0.0.132:8443. Komodo-name still `pc6-ct155-unifi` (unchanged), not Komodo-managed (manual stack). |
| Paperless | pc9 CT154 | **Done (6. okt)** | Moved from pc6. 10.0.0.131:8000. n8n integration unaffected (over network). |
| Roon | pc9 CT152 | **Done (6. okt)** | Moved from pc6, started. 10.0.0.125. Mounts /music + /backup from Tower-media. |
| Immich | pc9 CT153 | **Done (6. okt)** | Moved from pc6. 10.0.0.127:2283, /dev/dri passthrough + /photos (Tower-photos NFS). |
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
- **Komodo-alert `pc6-ct103-node` er løst.** Var `ServerUnreachable` fra 4. oktober 13:59.
  Årsak: filbanen var aldri problemet — `run_directory` og `file_paths` var korrekte
  hele veien. Periphery på CT103 identifiserte seg fortsatt som `pc1-ct103-node`
  etter flyttingen til pc6. Løst ved å gi agenten navnet `pc6-ct103-node` og
  gjenskape Periphery. n8n-stacken kjører med n8n + postgres, begge friske.
  Se `docs/INVENTORY.md` — navnedriften er der ennå ikke ryddet.
- **Homepage GitOps: løst 4. oktober.** Mounten er nå hele mappa
  (`../homepage/config:/app/config:ro`), ikke enkeltfilen. `git pull` bytter ut
  filer med nye inoder, så en enkeltfil-bind-mount fortsatte å servere gammelt
  innhold. Konfigurasjonen kommer nå fra
  `/opt/komodo/stacks/pc6-ct109-homepage/homepage/config`, ikke `/opt/homepage`.
  Netdata-lenkene er live og verifisert via `/api/services`.
  Min tidligere notat om at `file_paths` var årsaken var feil — `file_paths` er
  for ekstra compose-filer, ikke datafiler. Se `pc6-ct109-homepage/README.md`.