# WAN offentlig IP-vakt

**Workflow-id:** `TgkM1U6Fj2MW8X5G`
**Eksport:** `workflows/wan-offentlig-ip-vakt.json`
**Status:** aktiv (hver 6. time)

## Hva den gjør og hvorfor

WAN er DHCP fra NextGenTel, så den offentlige IP-en (nå `89.10.228.222`) kan
bytte seg ut uten forvarsel. Da bryter ekstern Emby-tilgang hvis dynamisk DNS /
portforward peker på den gamle adressen.

Workflowen henter offentlig IP hver 6. time og varsler iPhone kun når den har
endret seg fra forrige kjente verdi.

## Node-graf (5 noder)

| Node | Type | Rolle |
|---|---|---|
| Hver 6. time | scheduleTrigger | Trigger, `hoursInterval: 6` |
| Hent offentlig IP | httpRequest | GET `https://api.ipify.org?format=json` → `{"ip":"..."}` |
| Har IP-en endret seg? | code | Sammenligner med forrige kjøring, skriver `changed` (1/0) |
| Endret? | if | `changed > 0` → videre, ellers stopp |
| Varsle iPhone | httpRequest | POST til HA `notify/mobile_app_1_iphone_r` |

## Nøkkelmekanisme: `$getWorkflowStaticData`

n8n «glemmer» alt mellom hver kjøring. Code-noden lagrer siste IP i workflowens
statiske data og henter den neste gang:

```js
const sd = $getWorkflowStaticData('global');
const current = String($json.ip ?? '').trim();
const prev = sd.lastIp;
const changed = (current !== '' && prev !== undefined && current !== prev) ? 1 : 0;
sd.lastIp = current;
return [{ json: { ip: current, prevIp: prev ?? null, changed } }];
```

Første kjøring (`prev === undefined`) gir `changed = 0`: den bare etablerer
utgangspunktet uten å varsle. Varselet skjer først når IP-en faktisk avviker.

## Varslingsmål

`notify/mobile_app_1_iphone_r` (Home Assistant). Kun når `changed > 0` — altså
en reell endring, ikke ved hver kjøring.

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| HA long-lived token | Bearer-token | Notify-nodens `Authorization`-header (`REDACTED_HASS_TOKEN` i eksporten) |
| ipify.org | ekstern IP-tjeneste | offentlig, ingen nøkkel |

**Merk:** ipify er en tredjepart. Hvis den er nede (eller WAN er nede), feiler
`Hent offentlig IP` og `$json.ip` blir tom — code-noden gir da `changed = 0` og
varsler ikke. WAN-nedetid fanges i stedet av tjenestevakten.

## Gjenoppretting

1. **Workflows → Import from File**, velg
   `workflows/wan-offentlig-ip-vakt.json`.
2. I `Varsle iPhone`-noden: sett `Authorization`-header til
   `Bearer <reell HA-token>`.
3. Aktiver.

## Til å leke med (læring)

- Bytt `hoursInterval: 6` til `1` for timevis sjekk.
- Endre `notify/mobile_app_1_iphone_r` til iPad (`mobile_app_roger_sin_ipad_mini`)
  for å se hvordan du styrer hvilken enhet som varsles.
- Bytt `https://api.ipify.org` med `https://checkip.amazonaws.com` og se
  at node 2 må håndtere plain text i stedet for JSON.