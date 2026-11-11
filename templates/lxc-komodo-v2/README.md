# Docker LXC + Komodo V2 – standard (fra 10. nov 2026)

Alle nye Docker-arbeidslaster får sin egen unprivileged Debian 13-LXC, registrert i
Komodo med **Periphery som Docker-container** (fra 11. nov; systemd-varianten er avviklet for nye CT-er). Applikasjonen deployes som en Komodo-stack fra dette
repoet. Første CT etter denne malen: `pc8-ct126-netalertx`.

## Navn

- **Komodo-server og stack:** `<node>-ct<id>-<tjeneste>`, f.eks. `pc8-ct126-netalertx`
- **Mappe i repoet:** samme navn, med `docker-compose.yml` (og gjerne `README.md`)
- **Vertsnavn i CT-en:** bare tjenesten, f.eks. `netalertx`

IP-adressen står i Proxmox-beskrivelsen og README, ikke i navnet.

## Ny CT – én kommando på Proxmox-noden

```bash
ct-new <tjeneste> [ram_mb] [disk_gb] [kjerner]
ct-new uptime                     # neste ledige ID, 1 kjerne, 1024 MB, 8 GB, første ledige IP i .204-.254
ct-new immich 4096 32 2           # større CT
ct-new 130 immich                 # med bestemt ID
```

Størrelsen kan endres i Proxmox etterpå (Resources).

`ct-new` (`scripts/ct-new.sh`) gjør:

1. Tar neste ledige ID i klyngen (eller den du oppgir) og finner en ledig fast IP i `10.0.0.204–254`
   (utenfor Kea-poolen `.2–.99`; `.185–.199` er reservert for nettverksutstyr).
2. Lager CT-en: Debian 13 (laster ned template ved behov), unprivileged,
   `nesting=1,keyctl=1`, `onboot=1`, `vmbr0` med brannmur, gateway `10.0.0.1`,
   DNS `lan.local` + `10.0.0.115 10.0.0.118`, tidssone Europe/Oslo og nodens
   `authorized_keys`.
3. Starter den og kjører `ct-komodo` (under).

## Eksisterende CT – registrer i Komodo

```bash
ct-komodo <ctid> [tjeneste]       # tjeneste = CT-ens vertsnavn hvis utelatt
```

`ct-komodo` (`scripts/ct-komodo.sh`) gjør:

1. Proxmox: DNS, vertsnavn, `nesting/keyctl`, `onboot=1` (restart bare ved behov).
2. Kjører `scripts/ct-fix.sh` i CT-en (nettverk, DNS, apt-reparasjon, oppdatering).
3. Kjører `scripts/komodo-bootstrap.sh`: Docker CE + Periphery som container (`/opt/komodo/periphery`, compose fra denne mappa).
   Hoppes over hvis CT-en allerede kjører Periphery med samme navn. Stopper hvis det
   finnes en systemd-Periphery – to agenter på samme CT gir reconnect-løkke i Core.
4. Finnes `<navn>/docker-compose.yml` i repoet, opprettes stacken i Komodo og deployes.
   Ellers: lag mappen, og kjør `ct-komodo <ctid>` igjen.
5. Skriver ut ferdige linjer for Smokeping og nettverkskart.

## Oppdatering

Ny Komodo-versjon varsles av n8n («Komodo-versjonsvakt»). Oppgrader Core først, deretter
`ct-periphery-update --alle`. Se «Oppdatere Komodo» i `docs/ACCESS-RUNBOOK.md`.

## Hemmeligheter (aldri i Git – repoet er offentlig)

På hver node, mode 600:

- `/root/.config/komodo/onboarding.key` – onboarding-nøkkel (kopieres inn i CT-en og slettes etter bruk)
- `/root/.config/komodo/api.env` – `KOMODO_URL`, `KOMODO_API_KEY`, `KOMODO_API_SECRET` (for stack-opprettelse)

Kommandoene `ct-new` og `ct-komodo` ligger i `/usr/local/sbin/` på alle noder og henter
alltid siste skript fra `main`.

## Etter registrering

- Legg CT-en inn i Smokeping (`pc9-ct113-ntopng/smokeping/Targets`) og nettverkskartet.
- Media ligger på Tower og monteres inn ved behov; kopieres aldri.
- Nødretting av en CT som mangler oppdateringer eller har nettverksfeil: se
  «CT-fiks» i `docs/ACCESS-RUNBOOK.md`.

## Gammel metode (systemd) – 10. nov 2026

> 11. nov: standarden er snudd tilbake til Periphery-container for nye CT-er. CT-ene under kjører fortsatt systemd-Periphery og er ikke flyttet tilbake ennå. `ct-periphery-update` oppdaterer bare systemd-varianten.

CT-er med Periphery som Docker-container ble flyttet til systemd-Periphery med

```bash
ct-periphery-migrate <ctid> [nytt-servernavn]
```

Skriptet gjenbruker containerens private nøkkel og `root_directory` (`/opt/komodo`),
så Komodo ser samme server og alle stack-stier er uendret. App-containere kjører videre.
Den gamle Periphery-containeren stoppes med `restart=no` (beholdes for tilbakerulling).
Ruller automatisk tilbake hvis serveren ikke blir `Ok` innen 90 sekunder.

**Viktig (rettet 10. nov):** systemd-Periphery leser ellers nøkkelen fra
`${root_directory}/keys/periphery.key` og lager en *ny* nøkkel der når root er `/opt/komodo`.
Skriptet setter derfor `private_key = "file:/etc/komodo/keys/periphery.key"` og krever en fersk
«Logged in to Komodo Core» i loggen før det godtar migreringen (Komodo-status kan henge igjen fra
den gamle containeren).

Migrert: CT101, CT102 (pc1), CT103, CT106, CT111, CT115 (→ `pc7-ct115-unifi`),
CT120 (→ `pc6-ct120-monitoring`), CT200, CT203, CT220, CT250, CT310.
CT112 omdøpt til `pc7-ct112-ntp`.

**Unntak:** CT110 (Komodo Core) beholder Periphery fra Core sin egen compose
(`komodo-periphery-1`, kobler til `ws://core:9120`). Den deler nøkkelvolum med Core og
gjenskapes ved `docker compose up`; den tas ved neste Core-oppgradering.
