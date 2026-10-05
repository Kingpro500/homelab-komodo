# Daglig homelab-diagnose

**Workflow-id:** `pgl2MbPlYaqFVHY6`
**Eksport:** `workflows/daglig-homelab-diagnose.json`
**Status:** aktiv (kjørte 5. okt 08:15 uten inngripen)

## Hva den gjør

Kjører hver morgen kl. 08:15 og henter hele homelab-diagnosen fra Hermes'
audit-endepunkt på CT157, uten å holde noen av homelab-nøklene i n8n. Ruter
funn etter alvorlighetsgrad og sender kun push når det faktisk er noe nytt —
aldri en daglig «alt OK»-melding.

## Node-graf (9 noder)

| Node | Type | Rolle |
|---|---|---|
| Hver dag 08:15 | scheduleTrigger | Trigger, daglig 08:15 |
| Hent diagnose | httpRequest | GET `10.0.0.135:9118/audit` med `X-Audit-Token` |
| Er noe nytt? | if | `new_findings.length > 0` — false stopper med vilje |
| Er det kritisk? | if | `new_findings.some(f => f.severity === 'KRITISK')` |
| Push kritisk - iPhone | httpRequest | POST til HA `notify/mobile_app_1_iphone_r` |
| Push advarsel - iPad | httpRequest | POST til HA `notify/mobile_app_roger_sin_ipad_mini` |
| Hent audit for kritisk-sjekk | httpRequest | GET `/audit` på nytt for vedvarende funn |
| Er noe vedvarende kritisk? | if | `persistent_critical.length > 0` |
| Push vedvarende kritisk | httpRequest | POST til HA `notify/mobile_app_1_iphone_r` |

## Hva som utløser varsel

1. **Kritiske funn** → push til iPhone.
2. **Advarsler** → push til iPad (mindre forstyrrende).
3. **Vedvarende kritisk** (`persistent_critical`) → egen push, slik at et
   problem som står over 24 timer påminnes i stedet for å drukne i dagens
   ordinære melding. Deduplikering skjer i audit-endepunktet, ikke i n8n.

Ingen push døgnet rundt når alt er friskt — false-branchen er bevisst tom.

## Varslingsmål

- `mobile_app_1_iphone_r` (kritisk, vedvarende)
- `mobile_app_roger_sin_ipad_mini` (advarsel)

Begge er Home Assistant `notify`-tjenester. Endepunktene er
`http://10.0.0.7:8123/api/services/notify/<navn>`.

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| `X-Audit-Token` | Hermes' audit-token | `AUDIT_TOKEN` i Hermes `.env` (aldri i n8n-kroppen på disk her) |
| HA long-lived token | Bearer-token til HA | n8n-header, erstattes ved import (`REDACTED_HASS_TOKEN`) |
| Hermes-endepunkt | `http://10.0.0.135:9118` | `homelab-audit.service` (systemd, user scope) på CT157 |
| Home Assistant | `10.0.0.7:8123` | HA på pc8, VM100 |

Workflowen bruker **rå header-verdier** (auth `none`), ikke n8n credentials.
Derfor er de to hemmelighetene satt som plassholdere i eksportfilen.

## Gjenoppretting

1. I n8n: **Workflows → Import from File** og velg
   `workflows/daglig-homelab-diagnose.json`.
2. Åpne de tre `httpRequest`-nodene som har header-navn `X-Audit-Token`, og
   sett `value` til den reelle verdien fra Hermes `.env` (`AUDIT_TOKEN`).
3. Åpne de tre push-nodene (`Authorization`-header) og erstatt
   `Bearer REDACTED_HASS_TOKEN` med den reelle HA-tokenen.
4. Aktiver workflowen (eksporten importeres inaktiv — aktivering er et eget
   steg i n8n).

Anbefalt i stedet for punkt 2–3: opprett n8n-credentials for tokenene og la
nodene referere dem, men workflowen er i produksjon med rå headere og må ikke
endres uten en eksplisitt beslutning.

## Feilmoduser å kjenne til

- **`Graphql is offline`:** ikke et nettverksbrudd — Unraid Connect/PM2-bunten
  har hengt. Rettes med `unraid-api restart` på Unraid, ikke i n8n.
- **`Invalid API key`:** Unraid-nøkkelen i Hermes `.env` er utløpt eller
  ugyldig. Fornyes i Unraid under Settings → API.
- **Empty `data`:** endepunktet svarte uten `data`-felt — se audit-loggen på
  CT157, ikke n8n.