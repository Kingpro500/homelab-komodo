# Lagring — full-fremskrivning

**Workflow-id:** `O3FZ7CxnsEWGRfcZ`
**Eksport:** `workflows/lagring-full-fremskrivning.json`
**Status:** aktiv (daglig 08:30)

## Hva den gjør og hvorfor

Proxmox-NFS-volumene mot Unraid fylles – Tower (backups) står på ~97 % og
Tower-media på ~95 %. En fast terskel sier bare «fullt»; denne workflowen sier
**når** det blir fullt, slik at du kan rydde eller utvide mens det er tid.

Den logger `used_pct` per NFS-volum én gang i døgnet, regner ut veksthastigheten
(%/dag) over de siste dagene og projiserer hvor mange dager det er igjen.

## Node-graf (5 noder)

| Node | Type | Rolle |
|---|---|---|
| Hver dag 08:30 | scheduleTrigger | Trigger, daglig 08:30 |
| Hent volumstatus | httpRequest | GET `10.0.0.135:9118/storage` (Proxmox-volumene) |
| Logg og prosjekter | code | Lagrer historikk + regner vekstrate og dager-til-full |
| Fylles innen 60 dager? | if | `alerts.length > 0` → videre, ellers stopp |
| Varsle iPhone | httpRequest | POST til HA `notify/mobile_app_1_iphone_r` |

## Koden i `Logg og prosjekter`

```js
const sd = $getWorkflowStaticData('global');
const today = new Date().toISOString().slice(0, 10);
const hist = sd.hist || {};
const volumes = $json.storage.filter(s => s.plugintype === 'nfs' && s.used_pct >= 80);
const alerts = [];
for (const v of volumes) {
  // ... legg til dagens prøve, behold siste 60
  const win = arr.slice(-14);
  if (win.length < 5) continue;                       // trenger minst 5 prøver
  const rate = (last.used_pct - first.used_pct) / days;  // %/dag
  if (rate < 0.02) continue;                          // for svak vekst
  const daysToFull = Math.round((100 - last.used_pct) / rate);
  if (daysToFull <= 60) alerts.push({...});
}
sd.hist = hist;
return [{ json: { alerts } }];
```

Nøkkelpunkter:
- **`$getWorkflowStaticData('global')`** holder historikken mellom kjøringer
  (samme mekanisme som WAN-IP-vakten, men med en hel liste i stedet for én verdi).
- **Vekstrate over 14 dager**, og minimum 5 prøver før det varsles — den første
  uken gir altså ingen varsel, med vilje.
- **Tersklene:** kun NFS-volum over 80 %, vekst over 0,02 %/dag, og full om ≤ 60 dager.
- **Flat → stille.** Et volum som står på 97 % men ikke vokser (som Tower) gir
  ikke varsel — full-datoen kommer aldri.

## Varslingsmål

`notify/mobile_app_1_iphone_r` (Home Assistant). Kun når minst ett volum
projiseres fullt innen 60 dager. Tittel: «Lagring: N volum på vei til å fylles».

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| `X-Audit-Token` | Hermes' audit-token | `AUDIT_TOKEN` i Hermes `.env` |
| HA long-lived token | Bearer-token | Notify-nodens header (`REDACTED_*` i eksporten) |
| `/storage`-endepunkt | `http://10.0.0.135:9118/storage` | `homelab-audit.service` på CT157 |

## Gjenoppretting

1. **Workflows → Import from File**, velg `workflows/lagring-full-fremskrivning.json`.
2. Sett `X-Audit-Token` i `Hent volumstatus` og `Authorization` i `Varsle iPhone`
   til reelle verdier.
3. Aktiver. (Merk: historikken er tom etter import, så det varsles ikke før
   minst 5 daglige kjøringer er samlet inn.)

## Til å leke med (læring)

- Senk `daysToFull <= 60` til `30` for tidligere, mindre støyende varsel.
- Bytt `mobile_app_1_iphone_r` til iPad-en for å se effekten.
- Legg til `&& s.storage !== 'Tower'` hvis du vil ekskludere et volum.

## Oppgraderingsbane

For mer robust lagring av historikk (som overlever workflow-import og er lettere
å utforske), flytt historikken til Google Sheets/nedb via en n8n-integrasjon i
stedet for `$getWorkflowStaticData`. Samme kode, men `hist` blir en tabell.