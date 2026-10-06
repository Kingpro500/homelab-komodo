# Emby - overvaaking og autorestart

**Workflow-id:** `dK3dJJIQ7smvUy9v`
**Eksport:** `workflows/emby-overvaaking-autorestart.json`
**Status:** aktiv (hvert minutt)

## Hva den gjør og hvorfor

Overvåker Emby (10.0.0.150:8096, CT151 `emby-pc6` på pc6) kontinuerlig. Er
Emby utilgjengelig, varsler den iPhone **og** rebooter hele Emby-CT-en for å få
tjenesten opp igjen — mer robust enn å bare starte containeren på nytt, siden en
CT-reboot også rydder opp i alt som henger inne i CT-en.

For å unngå at n8n holder homelab-nøklene (HA-token, SSH-nøkkel til pc6), går
alle kall gjennom `homelab-audit`-serveren på `10.0.0.135:9118` (samme
arkitektur som `Nettverksovervaakning` og `Daglig homelab-diagnose`). n8n sender
kun `X-Audit-Token`; selve probingen, rebooten og iPhone-pushen skjer på
CT157 der nøklene ligger.

## Node-graf (7 noder)

| Node | Type | Rolle |
|---|---|---|
| Hvert minutt | scheduleTrigger | Trigger, `secondsInterval: 60` |
| Hent Emby-status | httpRequest | GET `/emby/status` → `{up, went_down, recovered}` |
| Gikk Emby ned? | if | `went_down == true` → reboot + varsel |
| Reboot Emby-CT | httpRequest | POST `/emby/restart` (med 15-min cooldown) |
| Varsle om nedetid | httpRequest | POST `/notify` → iPhone |
| Kom Emby tilbake? | if | `recovered == true` → tilbake-varsel |
| Varsle om tilbakekomst | httpRequest | POST `/notify` → iPhone |

## Nøkkelmekanisme: overgangsdeteksjon

Emby polles hvert minutt, men vi vil ikke spamme iPhone hvert minutt mens
tjenesten er nede. `emby_watch.py` på CT157 husker forrige tilstand og rapporterer
**overganger** i stedet for absolutt tilstand:

- `went_down: true` — første gang en oppe-tjeneste blir nede (utløser reboot + varsel)
- `recovered: true` — første gang en nede-tjeneste svarer igjen (utløser tilbake-varsel)

Mens Emby er nede i flere minutter, er `went_down` bare `true` på den første
sjekken; resten av tiden gir status-kallet `went_down: false`, så n8n gjør ingenting.

Liveness-endepunktet er `GET /System/Info/Public` → HTTP 200 = oppe (åpent uten
auth). `/health` gir 404 og er derfor ubrukelig som sjekk — derfor bruker vi
`/System/Info/Public`.

## Reboot med cooldown

`POST /emby/restart` rebooter CT151 med `pct reboot 151` (ikke bare
`docker restart emby`). docker er `enabled` i CT-en, og Emby har
`restartpolicy: unless-stopped`, så Emby (og tunarr) kommer opp automatisk etter
boot — bekreftet ved testre volt 6. okt: begge oppe igjen på ~17 s.

For å hindre restart-loop under en langvarig nedetid har `/emby/restart`
**15-min cooldown** (variabelen `RESTART_COOLDOWN_S = 900` i `emby_watch.py`,
siste omstartstid i `.emby_state.json`). Kalles rebooten for tidlig, returnerer
endepunktet `{"ok": false, "cooldown": true, "cooldown_remaining_s": ...}` og
n8n sender ikke en ny reboot.

## Varslingsmål

iPhone via Home Assistant. `/notify`-endepunktet kaller `notify_ha.py` → HA →
`mobile_app_1_iphone_r`. To typer:

- **Nedetid:** «Emby er nede - sender reboot»
- **Tilbakekomst:** «Emby er tilbake»

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| Audit-token | Bearer / `X-Audit-Token` | `REDACTED_AUDIT_TOKEN` i eksporten; ekte verdi i `/home/hermes/.hermes/.env` på CT157 (`AUDIT_TOKEN`) |
| `homelab-audit`-server | 10.0.0.135:9118 | systemd-enhet `homelab-audit.service` på CT157 |
| `emby_watch.py` | status()/restart() | `/home/hermes/.hermes/scripts/emby_watch.py` (importert av audit-serveren) |
| SSH til pc6 | root@10.0.0.120, nøkkel `~/.ssh/id_ed25519_hermes` | kun på CT157, aldri i Git |

## Gjenoppretting

1. **Workflows → Import from File**, velg
   `workflows/emby-overvaaking-autorestart.json`.
2. De fire nodene som ringer `10.0.0.135:9118` (status, reboot, 2 × notify):
   sett `X-Audit-Token` til `REDACTED_AUDIT_TOKEN` → den ekte `AUDIT_TOKEN`-verdien
   fra `.env` på CT157.
3. Aktiver.

## Til å leke med (læring)

- Bytt `secondsInterval: 60` til `300` for hvert 5. min.
- Endre cooldownen i `emby_watch.py` (`RESTART_COOLDOWN_S`) hvis 15 min føles
  for kort/langt.
- Vil du ikke reboote hele CT-en, bytt `pct reboot 151` til
  `pct exec 151 -- docker restart emby` i `emby_watch.py`.
