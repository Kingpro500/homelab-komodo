# Podgrab minnevakt

n8n-workflow (id `1XBR4tgHzIu57tra`, aktiv). Varsler tidlig når Podgrab lekker minne, før CT210 (`pc6-ct210-media-services`, 4 GB) går full.

- **Eksport:** [workflows/podgrab-minnevakt.json](../workflows/podgrab-minnevakt.json)
- **Trigger:** hvert 10. minutt, og POST `/webhook/podgrab-minnevakt-kjor` (manuell kjøring; sender bare varsel ved reelt funn).

## Bakgrunn
Podgrab brukte ca. 3 GB RSS i CT210 (kjent lekkasje) og sendte CT210 til 96 prosent minne. Compose har nå `mem_limit: 768m` (`pc6-ct109-media-automation`), så en lekkasje gir restart i stedet for at CT-en tømmes.

## Flyt
1. **Les container-metrikker:** `GET http://10.0.0.135:9120/metrics` (Hermes-eksportøren, ingen hemmeligheter). Metrikkene `komodo_container_mem_usage_bytes` og `komodo_container_mem_limit_bytes` (`server`, `container`) kommer fra Komodo `ListDockerContainers`-stats og caches 60 s i eksportøren.
2. **Vurder Podgrab-minne** (Code, kun lesing; listen `WATCH` kan utvides med flere containere):
   - **warn:** to målinger på rad på minst 60 prosent av taket, eller vekst over 100 MiB/time over minst 45 min (minst 6 prøver) og over 25 prosent av taket.
   - **crit:** minst 85 prosent av taket.
   - **restart:** forrige måling minst 70 prosent, nå under 30 prosent (OOM-kill / selvrestart).
   - **mangler:** metrikken finnes ikke i 3 kjøringer på rad (30 min).
   - **løst:** tilbake til ok etter warn/crit sender ett «tilbake til normalt».
3. **Send via homelab-alerts** (`POST /webhook/homelab-alerts`; telefon-push følger homelab-alerts sin stilleperiode 23–06 og timegrense).

## Dedupe
Per type (`warn`, `crit`, `restart`, `missing`) maks ett varsel per 6 timer (workflow static data). Historikk: siste 3 timer.

## Sikkerhet
Ingen restart, ingen stopp, ingen skriving. Workflowen har ingen credentials; eksporten inneholder ingen hemmeligheter (kontrollert).

## Avhengighet: eksportøren
`~/.hermes/scripts/homelab_metrics_exporter.py` (systemd user-tjeneste `homelab-metrics.service` på Hermes CT130) har fått `container_lines()`. Komodo-nøkkelen leses fra `~/.hermes/.env` og eksponeres aldri. Backup før endring: `homelab_metrics_exporter.py.bak-20261111-container-mem`. Prometheus beholder ikke disse metrikkene (keep-regex er `(emby_.*|proxmox_guest_.*)`); n8n leser eksportøren direkte.

## Test
Lokal scenetest av Code-noden (baseline, lav, warn, cooldown, crit, restart, løst, mangler, trend) og live-test av regex mot faktisk metrikkutdata. Faktisk n8n-kjøring via webhook: lesing OK, ingen varsel (Podgrab ca. 12 MiB av 768 MiB). Varselgrenen mot telefonen er ikke utløst med et ekte funn.
