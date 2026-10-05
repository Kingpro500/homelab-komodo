# Nettverksovervaakning

**Workflow-id:** `zu6Tg91HWtUaHI2M`
**Eksport:** `workflows/nettverksovervaakning.json`
**Status:** aktiv (to grener, to ulike frekvenser)

## Hva den gjør

To uavhengige grener på samme workflow:

1. **Timevis** (kl. `:05` hver time): henter kompakt nettverksstatus og
   varsler **kun** når det har dukket opp nye problemer siden sist.
2. **Dagsrapport** (kl. 08:00): henter full nettverksrapport, formaterer den
   og sender alt til iPad.

Begge henter fra Hermes-endepunktet på CT157 — ingen nettverks-/homelab-nøkler
ligger i n8n.

## Node-graf (8 noder)

| Node | Type | Rolle |
|---|---|---|
| Hver time | scheduleTrigger | Trigger, time `:05` |
| Hent nettverksstatus | httpRequest | GET `10.0.0.135:9118/network/status` |
| Er det nye problemer? | if | `new_problems.some(p => p.sev === 'KRITISK' \|\| p.sev === 'ADVARSEL')` |
| Push nytt nettverksproblem | httpRequest | POST til HA `notify/mobile_app_roger_sin_ipad_mini` |
| Hver dag 08:00 | scheduleTrigger | Trigger, daglig 08:00 |
| Hent full nettverksrapport | httpRequest | GET `10.0.0.135:9118/network` |
| Formater rapport | code | Bygger menneskelesbar tekst fra JSON |
| Push dagsrapport nettverk | httpRequest | POST til HA `notify/mobile_app_roger_sin_ipad_mini` |

## Hva som utløser varsel

- **Timevis:** kun `new_problems > 0` der alvorlighet er KRITISK eller
  ADVARSEL. INFO og uendret tilstand sender ingenting (dempet med vilje).
- **Dagsrapport:** alltid kl. 08:00, uavhengig av tilstand — tittel er
  `Nettverk: alt OK` når `all_clear`, ellers `Nettverk: N problemer`.

## Deduplikering

`new_problems` sammenlignes mot forrige kjøring i Hermes-endepunktet
(`~/.hermes/scripts/.net_endpoint_state.json` på CT157), ikke i n8n. En feil
som er meldt, meldes bare når den oppstår på nytt — ikke ved hver kjøring.

## Innhold i rapporten (fra `Formater rapport`)

```
Tjenester: 11/11
WAN: N hopp siste time, N sek nede
LAN: N enheter, M ARP-konflikt
Fysiske hopp siste døgn: igc0=0, igc1=N
Port-counters (CRC/drops): ikke tilgjengelig via OPNsense-API
[aktive problemer eller "Ingen aktive problemer."]
```

## Varslingsmål

`mobile_app_roger_sin_ipad_mini` — begge grener.

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| `X-Audit-Token` | Hermes' audit-token | `AUDIT_TOKEN` i Hermes `.env` |
| HA long-lived token | Bearer-token til HA | n8n-header (`REDACTED_HASS_TOKEN`) |
| Hermes-endepunkt (status) | `http://10.0.0.135:9118/network/status` | `homelab-audit.service` på CT157 |
| Hermes-endepunkt (full) | `http://10.0.0.135:9118/network` | samme tjeneste |

## Gjenoppretting

1. **Workflows → Import from File**, velg
   `workflows/nettverksovervaakning.json`.
2. Sett `X-Audit-Token` i de to hente-nodene til reell verdi fra Hermes `.env`.
3. Sett `Authorization`-header i de to push-nodene til
   `Bearer <reell HA-token>`.
4. Aktiver workflowen.

## Kjent begrensning

`Port-counters (CRC/drops)` er ikke tilgjengelig — OPNsense-API-et eksponerer
ikke interface-counters, og UniFi manglet SNMP (verifisert 4. okt). Først når
det er en lesende UniFi-bruker kan CRC-feil i EdgeSwitch/AC Pro måles. Rapporten
sier dette eksplisitt i stedet for å late som.