# Hermes-kø (`hermes-ko`)

Hermes-kø har to eksplisitte lane-workers: `infra` for Proxmox, Komodo og GitHub og
`general` for Home Assistant/AI og annet. Maksimalt én worker per lane og maksimalt
én worker per delt ressurs. Lane-låsen er alltid aktiv; `ressurser` er en ekstra lås.

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
nåværende avvik: `hermes-ko-general.timer` bruker `OnUnitInactiveSec=1min`.
Dermed er det én timerstyrt worker per lane; timerne skal ikke brukes til å starte
flere samtidige workers i samme lane.

Det finnes også deklarative filer for den gamle lane-løse `hermes-ko.service` og
`hermes-ko.timer`, men de skal være deaktivert når lane-timerne er aktive. Det
finnes ingen `ConcurrencyLimit`; n8n-lane-låsen er autoritativ, og samme lane kan
derfor ikke få to samtidige workers selv om timer-kall overlapper.

## Deler

| Fil | Installeres som |
| --- | --- |
| `hermes_ko.py` | CT130 `/home/hermes/.hermes/scripts/hermes_ko.py` |
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

Runtime-kilden er `pc7-ct130-hermes/hermes-ko/hermes_ko.py`, installert på CT130 som `/home/hermes/.hermes/scripts/hermes_ko.py`. Aktiv n8n-workflow `hermes-ko` bruker Code-noden fra `ko-n8n.js`. Før liveoppdatering tas backup under `~/.hermes/ko/`; rollback deaktiverer de nye timerne, gjenoppretter workflow-backup og forrige GitHub-versjon, og kontrollerer låser.


`ny` → `kjorer` → `venter_godkjenning`/`godkjent` → `ferdig`,
`ferdig_med_merknad`, `feilet` eller `parkert`. Ved livefeil deaktiveres begge
lane-timere, workflow-backup gjenopprettes via dokumentert n8n API-rute, og forrige
GitHub-versjon installeres. Deretter aktiveres gammel timer bare etter at workflow,
service-status og låser er kontrollert.
