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

CT130 installerer disse fire filene i `/etc/systemd/system/`:

- `hermes-ko-infra.service` → `hermes_ko.py run --lane infra`
- `hermes-ko-general.service` → `hermes_ko.py run --lane general`
- `hermes-ko-infra.timer` og `hermes-ko-general.timer` → hvert 2. minutt

Begge er `Type=oneshot`, `User=hermes` og `TimeoutStartSec=3h`. Det finnes ingen
`ConcurrencyLimit`; n8n-lane-låsen er autoritativ, og samme lane kan derfor ikke få
to samtidige workers selv om timer-kall overlapper. Den gamle `hermes-ko.timer` skal
være deaktivert før lane-timerne aktiveres.

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

## Status og rollback

`ny` → `kjorer` → `venter_godkjenning`/`godkjent` → `ferdig`,
`ferdig_med_merknad`, `feilet` eller `parkert`. Ved livefeil deaktiveres begge
lane-timere, workflow-backup gjenopprettes via dokumentert n8n API-rute, og forrige
GitHub-versjon installeres. Deretter aktiveres gammel timer bare etter at workflow,
service-status og låser er kontrollert.
