# Varsel-digest (hver 6. time)

Innført 19. nov 2026 etter ønske fra Roger: varsler skal bare komme hver 6. time, ikke fortløpende.

| | |
|---|---|
| Workflow | «Varsel-digest (hver 6. time)», id `BABunjhEF6aiM3Gu` |
| Kø | n8n Data Table `varsel_ko` (id `n1V4Pl8EKmfMY9L6`, kolonner `title`, `message`, `kilde`) |
| Inn | `POST http://127.0.0.1:5678/webhook/varsel-ko?kilde=<workflow / node>` med JSON `{title, message}` |
| Ut | kl. 00, 06, 12 og 18 (Europe/Oslo): én melding til Home Assistant `notify.mobile_app_1_iphone_r` |
| Kjør nå | `POST http://10.0.0.119:5678/webhook/varsel-digest-kjor` (sender bare hvis køen ikke er tom) |
| Eksport | [workflows/varsel-digest.json](../workflows/varsel-digest.json) |

## Slik virker den

1. Alle varselnoder som før sendte direkte til telefonen (Home Assistant `notify/mobile_app_*` eller
   Hermes `10.0.0.135:9118/notify`) poster nå til `varsel-ko`. Det gjelder 12 noder i 9 workflows:
   Lagring, WAN-IP, PC1 full heng, Pi-hole DNS failover, Homelab-ressurs-alarmer (alt som kommer via
   `homelab-alerts`, også NetAlertX, blaff-logger og Pinchflat), Daglig diagnose (3), Media health,
   Emby backup-mount og Nettverksovervåkning (2).
2. Hvert varsel blir én rad i `varsel_ko`. Data Table tåler samtidige skriv (staticData gjør ikke det).
3. Digesten henter alle rader, slår sammen like titler (antall + tidsrom), sorterer kritiske først,
   kutter ved ~3500 tegn, sender én melding og sletter deretter bare radene til og med høyeste id som
   ble sendt. Feiler sendingen, blir radene liggende til neste runde.
4. Tom kø = ingen melding.

Eksisterende stilleperiode (23–06) og timegrense i de enkelte vaktene ligger fortsatt foran køen.

## Nye varsler

Nye vakter skal poste `{title, message}` til `varsel-ko` og ikke til telefonen direkte. Bruk
`kilde=<workflow> / <node>` i URL-en, så det er lett å se hvor varselet kom fra.

## Gjenoppretting

Importer `workflows/varsel-digest.json`, opprett tabellen `varsel_ko` med kolonnene over og sett riktig
tabell-id i nodene «Legg i kø», «Hent kø» og «Tøm sendte». Koble «Send til iPhone» til credentialen
«Home Assistant Bearer (n8n)». n8n 2.x: etter endring via API må workflowen deaktiveres og aktiveres
igjen hvis `versionId` ≠ `activeVersionId`.

## Tilbakerulling

Backup av alle endrede workflows før omleggingen: `/root/claude-n8n-backup-20261119` på CT310.
