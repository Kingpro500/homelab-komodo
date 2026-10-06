# Homelab-ressurs-alarmer

**Workflow-id:** `kALMQJZ2VgJLSOHp`
**Eksport:** `workflows/homelab-ressurs-alarmer.json`
**Status:** aktiv (webhook, kalles av Alertmanager hvert 10. min)

## Hva den gjør og hvorfor

Tar imot Prometheus/Alertmanager-varsler (webhook `homelab-alerts`) og
videresender dem som lesbare push-varsler til telefonen. Kjerneposisjonen
`proxmox_guest_mem_used_bytes / total >= 90` gir alarmen `GuestMemoryHigh` for
gjestene som overvåkes.

## Node-graf (2 noder)

| Node | Type | Rolle |
|---|---|---|
| Webhook | webhook | `POST /webhook/homelab-alerts` — mottar Alertmanager-payload |
| Send til telefon | httpRequest | POST `/notify` → HA → iPhone |

## Viktig: `Send til telefon` peker på `body.alerts`, ikke `alerts`

Alertmanager-payloaden ligger slik i n8n: hele pakken med `headers`, `params`,
`query` og `body` settes på `$json`. Selve alarmene er i **`$json.body.alerts`**.

Den opprinnelige noden brukte `$json.alerts` — som er `undefined`. Da falt
uttrykket ned på `JSON.stringify($json)`, altså **hele webhook-pakken med
HTTP-headere**, rå dumps til telefonen. Det ga et uforståelig varsel som så ut
som en JSON-header-dump i stedet for «RAM høy: …». Rettet 6. okt til å lese
`$json.body.alerts` og til å bygge en lesbar tittel/melding.

### Nytt uttrykk i `Send til telefon`

```js
={{ JSON.stringify((() => {
  const b = $json.body || {};
  const a = b.alerts || [];
  if (!a.length) { return { title: 'Homelab-varsel', message: JSON.stringify(b) }; }
  const f = a[0];
  const resolved = b.status === 'resolved';
  const summary = (f.annotations && f.annotations.summary) || 'Alarm';
  const desc = (f.annotations && f.annotations.description) || '';
  return {
    title: (resolved ? '[LØST] ' : '[ALARM] ') + summary,
    message: (desc || summary) + (b.status ? ' (' + b.status + ')' : '')
  };
})())
```

Uttrykket er verifisert med `node --check` og mot mock-data av den faktiske
payloaden: `firing` → `[ALARM] RAM høy: Unraid-Tower (pc6)`, `resolved` →
`[LØST] RAM høy: …`. Verifiser alltid `$json.body.<felt>` når en webhook-nodes
payload ikke ender direkte på `$json` — nesting er det vanligste feilgrepet her.

## Varslingsmål

Telefon via HA (`/notify` → `notify_ha.py` → `mobile_app_1_iphone_r`).
Noden bruker bare `X-Audit-Token`; HA-tokenet ligger på CT157, ikke i n8n.

## Avhengigheter

| Avhengighet | Verdi | Hvor den bor |
|---|---|---|
| Audit-token | `X-Audit-Token` | `REDACTED_AUDIT_TOKEN` i eksporten; ekte verdi i `/home/hermes/.hermes/.env` på CT157 (`AUDIT_TOKEN`) |
| `homelab-audit`-server | 10.0.0.135:9118 | systemd-enhet på CT157 |
| Alertmanager | sender til `/webhook/homelab-alerts` (10.0.0.119:5678) | konfigurert i Prometheus/Alertmanager på CT157 |

## Gjenoppretting

1. **Workflows → Import from File**, velg `workflows/homelab-ressurs-alarmer.json`.
2. I `Send til telefon`: sett `X-Audit-Token` til `REDACTED_AUDIT_TOKEN` → den
   ekte `AUDIT_TOKEN`-verdien fra `.env` på CT157.
3. Aktiver, og bekref at Alertmanager sender hit — test med en providert
   Alertmanager-payload (`status: firing` + `alerts[0].annotations`).