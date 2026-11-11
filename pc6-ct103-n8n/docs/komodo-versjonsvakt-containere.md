# Komodo-versjonsvakt - containere

n8n-workflow (id `eMw6l7rR36t7v9gu`, aktiv). Sammenligner installert versjon for kjørende Docker-containere (hentet via Komodo API) med siste GitHub-release, og mater «Versjoner»-panelet i nettverkskartet.

## Flyt
- **Daglig 05:15** (eller POST `/webhook/versjoner-oppdater`) → *Samle versjoner* (Code): ListServers → ListDockerContainers → InspectDockerContainer, slår opp image→GitHub-repo (tabell `GH` i koden), sammenligner. Resultat lagres i workflow static data.
- **GET `/webhook/versjoner`** → returnerer siste resultat som JSON (CORS `*`). Nettverkskartet (`http://10.0.0.124:3020/`) henter dette klient-side.
- *Samle versjoner* → **homelab-alerts**: varsler kun om containere som er *nye* utdaterte (dedupe på navn+server+nyeste versjon, lagret i static data). Første kjøring varslet alle eksisterende.

## Status
grønn = installert ≥ nyeste, rød = eldre, grå = ukjent (ingen tag/label eller ikke i `GH`-tabellen). Legg nye images i `GH` i Code-noden for å få dem sjekket.

## Hemmeligheter
Komodo API-nøkkel/-hemmelighet og GitHub-token ligger i Code-noden i n8n (eksporten har `REDACTED_*`). Komodo-nøkkelen bør være read-only.

## Erstatter
Tidligere Python-skript `versjoner.py`/`pushver.sh` + cron på Hermes-maskinen (fjernet).
