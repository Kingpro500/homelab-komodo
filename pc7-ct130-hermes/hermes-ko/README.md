# Hermes-kø (`hermes-ko`)

Hermes-kø har seks lanes (se under). `infra` har **tre samtidige plasser** fra 17. nov 2026,
de andre én. Maksimalt én worker per delt ressurs: to oppgaver med samme `ct:<id>` kjører
aldri samtidig, mens oppgaver på ulike CT-er går parallelt. Køstatus ligger i SQLite på
CT130 (`hermes-ko-store.service`), ikke i n8n.

## Datamodell og låser

Nye oppgaver har `kategori: infra|general` og `ressurser`, for eksempel
`["ct:130", "repo:homelab-komodo", "ha:home-assistant"]`. Ressursnavn normaliseres
til små, sanerte nøkler. Manglende kategori migreres deterministisk til `general` og
logges på oppgaven. Ugyldig kategori avvises uten at oppgaven opprettes eller mistes.

`next` mottar `lane` og `worker_id`, henter høyst én ledig oppgave og returnerer
`worker_id` og `lock_id`. Den atomiske state-operasjonen reserverer både lane og alle
ressurser. `update`, ferdig/feil-overgang, `reject` og eksplisitt `retry` krever samme
worker- og lock-id. Feil id avvises. Stale `kjorer` blir `feilet` med tydelig årsak;
lås- og workerhistorikk beholdes. Retry er eksplisitt og atomisk med samme lock-id.

## Systemd som faktisk skal kjøre

CT130 installerer én `Type=oneshot`-service og én timer for hver av de seks støttede
lanes i `/etc/systemd/system/`. Alle servicefilene kjører som `User=hermes` med
`TimeoutStartSec=3h` og følgende eksakte `ExecStart`:

- `hermes-ko-infra.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane infra`
- `hermes-ko-general.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane general`
- `hermes-ko-diagnostics.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane diagnostics`
- `hermes-ko-file-read.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane file-read`
- `hermes-ko-network-map-read.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane network-map-read`
- `hermes-ko-inventory.service` → `/usr/bin/python3 /home/hermes/.hermes/scripts/hermes_ko.py run --lane inventory`

De tilhørende timerfilene er `hermes-ko-infra.timer`, `hermes-ko-general.timer`,
`hermes-ko-diagnostics.timer`, `hermes-ko-file-read.timer`,
`hermes-ko-network-map-read.timer` og `hermes-ko-inventory.timer`. De bruker
`OnBootSec=3min`, `Unit=<lane-service>` og `OnUnitInactiveSec=2min`, med ett
avvik: `hermes-ko-general.timer` bruker `OnUnitActiveSec=1min` (satt av k90,
17. nov 2026). Den teller fra at workeren startet; `Type=oneshot` hindrer dobbeltstart.
Dermed er det én timerstyrt worker per lane; timerne skal ikke brukes til å starte
flere samtidige workers i samme lane.

Det finnes også deklarative filer for den gamle lane-løse `hermes-ko.service` og
`hermes-ko.timer`, men de skal være deaktivert når lane-timerne er aktive. Det
finnes ingen `ConcurrencyLimit`; n8n-lane-låsen er autoritativ, og samme lane kan
derfor ikke få to samtidige workers selv om timer-kall overlapper.

## Deler

| Fil | Installeres som |
| --- | --- |
| `hermes_ko.py` | CT130 `/home/hermes/.hermes/scripts/hermes_ko.py` (worker og CLI) |
| `hermes_ko_store.py` | CT130 `/home/hermes/.hermes/scripts/hermes_ko_store.py` (kø-API `http://10.0.0.135:9121/queue`) |
| `hermes-ko-store.service` | CT130 `/etc/systemd/system/`, alltid på |
| `hermes-ko-infra-2/-3.service` / `.timer` | CT130 `/etc/systemd/system/`, plass 2 og 3 i infra |
| `ko-n8n.js` | Code-noden «Kø» i aktiv workflow `hermes-ko` |
| `hermes-ko-*.service` / `.timer` | CT130 `/etc/systemd/system/` |

Aktiv workflow må sikkerhetskopieres før endring og kontrollhashes mot `ko-n8n.js`
etter oppdatering. Backup skal ligge under `~/.hermes/ko/`, aldri i Git.

## Bruk

```sh
python3 ~/.hermes/scripts/hermes_ko.py list
python3 ~/.hermes/scripts/hermes_ko.py get k3
python3 ~/.hermes/scripts/hermes_ko.py add < oppgave.json
python3 ~/.hermes/scripts/hermes_ko.py retry k3
```

CLI viser kategori/lane, worker og sanerte ressurser, men aldri tokens,
kontrollkommandoer eller hemmeligheter. Eksisterende statusspor beholdes, inkludert
`k65`, `k66` og `k70`.

## Kontroll

Kontroller at lane- og ressursimplementasjonen finnes i alle tre leveransene:

```sh
set -eu
ssh pc6 'test -f /root/claude-work/homelab-komodo/pc7-ct130-hermes/hermes-ko/hermes_ko.py'
ssh pc6 'grep -Eiq "lane|kategori|ressurs|resource" /root/claude-work/homelab-komodo/pc7-ct130-hermes/hermes-ko/hermes_ko.py'
ssh pc6 'grep -Eiq "lane|kategori|ressurs|resource" /root/claude-work/homelab-komodo/pc7-ct130-hermes/hermes-ko/ko-n8n.js'
ssh pc6 'test -f /root/claude-work/homelab-komodo/pc7-ct130-hermes/hermes-ko/README.md'
```

## Implementasjon av read-only lanes

Køen støtter `infra`, `general`, `diagnostics`, `file-read`, `network-map-read` og `inventory`. De fire siste er read-only og skal bare undersøke levende tilstand; de skal aldri skrive, deploye, restarte eller endre/publisere kartet. Lane-låsen serialiserer samme lane, mens normaliserte ressurser sperrer delte ressurser mellom lanes. Ugyldig kategori avvises uten å miste oppgaven.

Feiler kontrollkommandoen i en read-only lane, gjør workeren **ikke** noe retteforsøk; oppgaven ender som `feilet` med kontrollutskriften som funn. (Før 19. nov 2026 fikk retteforsøket ingen lane-sperre, og k162 i `inventory` endret Pi-hole-DNS på CT101/CT103.)

Runtime-kilden er `pc7-ct130-hermes/hermes-ko/hermes_ko.py`, installert på CT130 som `/home/hermes/.hermes/scripts/hermes_ko.py`. Aktiv n8n-workflow `hermes-ko` bruker Code-noden fra `ko-n8n.js`. Før liveoppdatering tas backup under `~/.hermes/ko/`; rollback deaktiverer de nye timerne, gjenoppretter workflow-backup og forrige GitHub-versjon, og kontrollerer låser.


`ny` → `kjorer` → `venter_godkjenning`/`godkjent` → `ferdig`,
`ferdig_med_merknad`, `feilet` eller `parkert`. Ved livefeil deaktiveres begge
lane-timere, workflow-backup gjenopprettes via dokumentert n8n API-rute, og forrige
GitHub-versjon installeres. Deretter aktiveres gammel timer bare etter at workflow,
service-status og låser er kontrollert.

## Kontrollørens dom (instruks til alle LLM-er som bruker køen)

Gjelder fra 17. nov 2026. Instruksen til modellene står i promptene i `hermes_ko.py`
(`REGLER`, `p_forslag`, `p_vurder`, `p_utfor`, `p_slutt`). Endres oppførselen, endres
promptene der og dette avsnittet i samme PR.

Kontrolløren gir én av tre dommer på et forslag:

| Dom | Når | Hva skjer |
| --- | --- | --- |
| `DOM: GODKJENT` | Ingen av de fem avvisningsgrunnene gjelder | Utføres. Linjer som begynner med `VILKÅR:` følger med til utføreren og skal følges. |
| `DOM: AVVIST` | Bare av de fem grunnene under | Ett nytt forslag. I runde to ser kontrolløren sin forrige vurdering og skal bare sjekke om den er løst. Avvist to ganger gir `parkert`. |
| `DOM: BLOKKERT` | Feilen ligger i oppgaven, ikke i forslaget | `parkert` med én gang, sammendrag `trenger beslutning: …`. Roger må bestemme. |

De fem avvisningsgrunnene: forslaget (1) bryter en fast regel, (2) gjør mer enn oppgaven
ber om, (3) bygger på en faktafeil kontrolløren selv har kontrollert, (4) endrer noe uten
å si hvordan det rulles tilbake, eller (5) vil ikke få kontrollkommandoen til å gå.
Manglende detaljer og ønsker om ekstra tester, backup eller fremgangsmåter som ikke står
i reglene eller oppgaven er ikke avvisningsgrunn; de skrives som `VILKÅR:`.

Hvor begrunnelsen står: `hermes_ko.py get <id>` viser sammendraget
(`forslaget ble avvist to ganger av kontrolløren: <grunn>` eller
`trenger beslutning: <spørsmål>`). Hele vurderingen for hver runde ligger i
oppgavens hendelseslogg (`events` i `~/.hermes/ko/hermes-ko.sqlite3`).

### Til deg som skriver oppgaver (Claude, Codex, Hermes)

- Kontrollkommandoen kjøres på CT130 som `hermes`. Filer på andre CT-er må leses med
  `ssh pc6 'pct exec <ctid> -- …'`. En kommando som tester en sti som bare finnes på en
  annen CT, feiler alltid, og oppgaven ender som `feilet` selv om arbeidet er gjort.
- Oppgaveteksten må stemme med virkeligheten (riktig direktiv, filnavn, node). Stemmer
  den ikke, gir kontrolløren `BLOKKERT` og oppgaven venter på Roger.
- Én CT per oppgave, og før CT-en opp i `ressurser` (`ct:<id>`), så ulike CT-er kan gå
  parallelt og samme CT aldri får to oppgaver samtidig.
- Systemd må kalle workeren med `run --lane <navn>`. Til og med 16. nov 2026 ble dette
  lest som `general` for alle lanes, så bare general-lanen hentet oppgaver (rettet i PR 285).

### Varsling og dagsrapport (fra 17. nov 2026)

Køen sender **ingen melding per oppgave**. Telefonvarsel går bare når Roger må bestemme
noe: en oppgave får `DOM: BLOKKERT` (parkert med `trenger beslutning: …`) eller settes til
`venter_godkjenning`. Alt annet samles i én dagsrapport kl. 06:00 norsk tid:

- `hermes-ko-rapport.timer` (`OnCalendar=*-*-* 06:00:00 Europe/Oslo`, `Persistent=true`)
  starter `hermes-ko-rapport.service`, som kjører `hermes_ko.py rapport`.
- Rapporten gir siste døgn (ferdig, med merknad, feilet, parkert), hva som står i kø nå,
  alt som venter på Roger, og feilet/parkert med grunn. Maks 700 tegn til telefonen; hele
  teksten står i journalen (`journalctl -u hermes-ko-rapport`).
- `hermes_ko.py rapport --vis` skriver rapporten uten å sende den.

Begge går via n8n `homelab-alerts` (vedleggsformatet `attachments: [{title, text}]`).
n8n slipper ikke telefonvarsler gjennom 23–06 og maks ett i timen. Et beslutningsvarsel
som faller bort der, kommer med i neste dagsrapport. Unngå ordene «new device» og
«ny enhet» i titler; n8n stopper slike meldinger.

Ikke lag egne overvåkingsløkker (`while sleep …; hermes_ko.py get kN`) eller cron-jobber
per oppgave. De ble stående i dager (k87-løkken avsluttet aldri fordi den ikke kjente
igjen `ferdig_med_merknad`) og ble fjernet 17. nov 2026.

### Køtjenesten (SQLite) og parallellitet

Filene i denne mappen er det som kjører på CT130 (kontrollert likt 17. nov 2026).
Databasen er `~/.hermes/ko/hermes-ko.sqlite3` (0600, aldri i Git). Ta backup med
SQLite sin backup-funksjon før endringer; kopier ikke filen mens tjenesten skriver.

- **Plasser:** `SLOTS = {"infra": 3}` står både i `hermes_ko.py` og `hermes_ko_store.py`,
  og det må finnes like mange timere (`hermes-ko-infra.timer`, `-2`, `-3`). Endres tallet,
  endres alle tre steder i samme PR.
- **Forslag og vurdering lagres** (`proposal`, `review`). En oppgave med
  `godkjenning: claude` stopper i `venter_godkjenning`; `hermes_ko.py approve <id>` gjør
  den `godkjent`, og neste worker utfører det lagrede forslaget med kontrollørens `VILKÅR:`.
- **Død worker:** finnes ikke prosessen bak `worker_id` lenger, settes oppgaven til
  `feilet` og lanen frigis ved neste kall til køen, ikke etter tre timer. Tre-timersregelen
  gjelder fortsatt for worker-id-er som ikke er en prosess på CT130.
- **Ingenting blokkerer:** `parkert`, `feilet`, `venter_godkjenning` og `ferdig` slipper
  alle låser med en gang.
