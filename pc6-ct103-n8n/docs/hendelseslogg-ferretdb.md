# Hendelseslogg - FerretDB

**Workflow-id:** `mUJE2QbmK08wAlys`
**Eksport:** `workflows/hendelseslogg-ferretdb.json`
**Status:** aktiv (webhook, POST `/webhook/events`)

## Hva den gjør og hvorfor

Samlingspunktet for alle feil/tilstander fra nettverket. I stedet for push-varsler
som forsvinner, sender kildene (Alertmanager, OPNsense-vakta, Emby, audit-serveren
osv.) en hendelse hit, n8n normaliserer den til et fast skjema, og lagrer den i en
ferretDB-kolleksjon — som igjen ligger i postgres. Resultatet er en søkbar
hendelseslogg du kan jobbe i når du er hjemme, i stedet for å gå glipp av varsler.

## Arkitektur

```
kilde (Alermanager/OPNsense/Emby/...)  ──POST──▶  /webhook/events  (n8n)
                                                          │  Normaliser hendelse (Code)
                                                          ▼
                                              MongoDB insert  "events"
                                                          │
                                                          ▼
                              FerretDB n8n-ferretdb (CT103) ──MongoDB URI──▶ mongodb://ferretdb:27017
                                                          │  backend
                                                          ▼
                              n8n-postgres → database homelab_events → schema homelab_events
```

- n8n og FerretDB er i samme compose-stack på CT103, så FerretDB nås med bare
  `ferretdb:27017` innen nettverket — ingen port eksponert ut.
- FerretDB skriver til postgres-databasen `homelab_events` (opprettet 6. okt).
- MongoDB-kolleksjon `events` → postgres-tabell `homelab_events.events_<hash>`.

## Node-graf (3 noder)

| Node | Type | Rolle |
|---|---|---|
| Webhook hendelser | webhook | POST `/webhook/events` |
| Normaliser hendelse | code | Validerer og trekker ut standardfelter fra vilkårlig payload |
| Lagre i FerretDB | mongoDb | insert i kolleksjon `events` |

## Dokument-skjema (standardfelter)

Normaliserings-noden skriver alltid disse feltene, så alle kilder får ensartet
form uansett hvordan de sender:

| Felt | Kilde i payloaden |
|---|---|
| `source` | `body.source` / `body.job` / `$json.source` |
| `type` | `body.type` / `body.alertname` / `body.status` |
| `severity` | `body.severity` / `alerts[0].labels.severity` |
| `title` | `body.title` / `alerts[0].annotations.summary` |
| `message` | `body.message` / `body.msg` / `alerts[0].annotations.description` |
| `host` | `body.host` / `body.instance` |
| `at` | `new Date().toISOString()` (mottatt-tidspunkt) |
| `details` | rå payload som JSON-streng |

## Viktig: MongoDB-noden bruker `fields`, ikke `document`

n8n sin MongoDB-node (typeVersion 2) bygger innsettingen fra parameteren
`fields` — en **kommaseparert liste over feltnavn** som hentes fra inngående
`$json`. Den tar **ikke** et `document`-objekt. Feil: å sette `document` gir bare
`_id` skrevet, ingenting annet. Riktig: Code-noden produserer et objekt, og
`fields` er `source,type,severity,title,message,host,at,details`.

## FerretDB-oppsett

Ny tjeneste i `docker-compose.yml`:

```yaml
  ferretdb:
    image: ghcr.io/ferretdb/ferretdb:1
    container_name: n8n-ferretdb
    restart: unless-stopped
    command:
      - "--postgresql-url=postgres://n8n:${N8N_POSTGRES_PASSWORD}@postgres:5432/homelab_events"
      - "--listen-addr=0.0.0.0:27017"
```

Tre fallgruver som kostet tid (6. okt):

- **FerretDB v1 krever doble bindestreker** (`--postgresql-url`, ikke
  `-postgresql-url` som eldre oppsett brukte). Enkel `-` gir `unknown flag -p`.
- **Må lytte på `0.0.0.0:27017`**, ikke default `127.0.0.1` — ellers er den
  ikke nåbar fra n8n-containeren.
- **Slett aldri Mongo-kolleksjoner med postgres-DROP direkte.** FerretDB cacher
  tabellnavnet i metadata; en direkte DROP gir `relation ... does not exist`
  neste insert. Riktig: dropp hele schemaet (`DROP SCHEMA ... CASCADE;
  CREATE SCHEMA ...`) og restart FerretDB-containeren, eller slett via
  MongoDB-protokollen (en `drop`-operasjon). Verifisert: restart etter
  schema-nullstilling får FerretDB til å opprette kolleksjonen fritt.

## Varsling tilknytning

Dette er *datalagring*, ikke varsling. Varslingen (→ iPhone) skjer fortsatt i
«Homelab-ressurs-alarmer»-workflowen. **Fra 6. okt 2026 logger to kilder også
inn i hendelsesloggen**, ved siden av varslingen:

- **Homelab-ressurs-alarmer** (webhook `homelab-alerts`): Webhook → `Send til
  telefon` (iPhone) **og** `Logg hendelse` (parallell) → POST `/webhook/events`.
- **Emby - overvaaking og autorestart**: `Varsle om nedetid` → `Logg nedetid`,
  og `Varsle om tilbakekomst` → `Logg tilbakekomst`.

**Fan-out-felle:** når én node skal videresende til to parallelle noder, må
begge grenene ha `"index": 0` (kilde-output-branch). En gren med `"index": 1`
kjører men får *ingen* data (tom utgang) — ser ut som suksess men skriver
ingenting. Rettet for `res`-workflowen; verifisert: Alertmanager-hendelse landet
i FerretDB med `source=alertmanager`.

### Vakt-script på CT157 logger også inn (via `log_event.py`)

`~/.hermes/scripts/log_event.py` er en best-effort POST til `/webhook/events`.
Kalt fra (6. okt 2026):

- **`service_watch.py`** — logger hvert **fresh** problem (etter `down_repeat=2`),
  takket i `build()`. Ikke suppressed-tellinger, så loggen holdes ren.
- **`opnsense_wan_watch.py`** — `wan-down` / `wan-unstable` ved terskel.
- **`opnsense_arp_watch.py`** — `arp-conflict` per IP.

`log_event()` svelger feil (aldri krasj vakt-scriptet). Nøkkel-args: `source`,
`type`, `severity` (info/warning/critical), `title`, `message`, `host`,
`details`. Verifisert: ARP-konflikt og testhendelse landet i FerretDB.

## Avhengigheter

| Avhengighet | Verdi |
|---|---|
| MongoDB-credential (n8n) | `FerretDB homelab_events` → `mongodb://ferretdb:27017` |
| FerretDB | container `n8n-ferretdb`, backend `homelab_events` i n8n-postgres |
| database | `homelab_events` (owner: n8n) |
| webhook-pat | `/webhook/events` på 10.0.0.119:5678 |

## Gjenoppretting

1. **Workflows → Import from File**, velg `workflows/hendelseslogg-ferretdb.json`.
2. I `Lagre i FerretDB`: velg MongoDB-credentialen `FerretDB homelab_events`
   (eller opprett på nytt med URI `mongodb://ferretdb:27017`).
3. Aktiver. Test med: `curl -X POST http://10.0.0.119:5678/webhook/events -H
   'Content-Type: application/json' -d '{"source":"test","message":"hei"}'`.

## Til å leke med (læring)

- Post et Alertmanager-eksempel og se hvordan `type` (alertname) og `severity`
  utledes: `{"status":"firing","alerts":[{"labels":{"alertname":"X","severity":"warning"},"annotations":{"summary":"S","description":"D"}}]}`.
- Endre `fields` i MongoDB-noden hvis du legger til et felt i Code-noden.
- Les loggen via FerretDB API (`mongo`-kompatibelt) eller rett fra postgres:
  `SELECT _jsonb FROM homelab_events.<tabell>`.
