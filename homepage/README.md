# pc6-ct109-homepage

Homepage (gethomepage.dev) — homelab-dashbordet på `10.0.0.128:3009`, pluss en
liten kontroll-API (`dockctl`) for å starte/stoppe/restarte containere.

## Tjenester

| Container | Havn | Rolle |
|---|---|---|
| `homepage` | 3009→3000 | Hoved-dashbordet |
| `dockctl` | 3015 | Start/stop/restart-panel for alle CT109-containere |

## Live status (nativt)

Homepage deler CT109s `docker.sock` (read-only). Hver CT109-tjeneste i
`config/services.yaml` har derfor:

```yaml
        server: ct109
        container: <containernavn>
```

Det gir et live kjørende/stoppet-merke på kortet, og å klikke på status-merket
viser CPU/RAM/nettverk (`showStats: true` i `settings.yaml`). Docker-serveren
er definert i `config/docker.yaml`.

### Hvorfor ikke alle tjenester har det

`socket: /var/run/docker.sock` i `docker.yaml` ser KUN containerne på CT109
(10.0.0.128). Tjenester på andre CT-er (Immich .127, Emby .150, Paperless .131,
n8n .119, NetBox/Komodo .117 …) ligger på andre Docker-demons og viser derfor
ikke container-status her — bare lenke + beskrivelse.

## dockctl — start/stop/restart-knapper

gethomepage har **ingen** innebygde start/stop/restart-knapper (feature request
#725 er avvist). I stedet kjører en liten Node-server (`dockctl/server.js`,
ingen avhengigheter) som snakker direkte med docker.sock:

- `GET  /`                          → kontrollpanel (ber om token, lagrer i localStorage)
- `GET  /api/containers`            → `[{name, state}]` for alle containere
- `POST /api/containers/<navn>/`<br>`start|stop|restart` → utfører handlingen

Panel-tilen «Docker-kontroll» i Homepage åpner `http://10.0.0.128:3015/`.
Status oppdateres hvert 5. sekund; token lagres i nettleseren.

### Sikkerhet / token

Alle `/api/*`-kall krever `Authorization: Bearer <CONTROL_TOKEN>` med
timing-safe sammenligning. `.env` er gitignored og token ligger i Komodo
stack-miljøet:

1. **Komodo → `pc6-ct109-homepage` → stackens miljøvariabler**: legg til
   `CONTROL_TOKEN` med en verdi du velger selv.
2. Redeploy stacken.

Uten `CONTROL_TOKEN` starter **ikke** `dockctl`-containeren i det hele tatt
(`${CONTROL_TOKEN:?…}` i `docker-compose.yml`) — fail-closed. Homepage-kortet
som er knyttet til `container: dockctl` viser da «stoppet», men Homepage selv
påvirkes ikke.

### Verifisert (6. okt 2026)

`server.js` testet end-to-end mot den ekte docker.sock på CT109 (med kaste-
containere): restart→running, stop→exited, start→running, 404 på ukjent
container, 401 uten/fell-token. Konfig: `docker compose config -q` OK.

## Hastighetsmetre (internett ned/opp)

To speedtest-kilder på dashboardet, begge nøkkel-hvit uten passord:

- **Speedtest Tracker** (`.128:8765`, LinuxServer/alexjustesen) → `widget type: speedtest`,
  `version: 1` (kaller `/api/speedtest/latest`, ingen API-nøkkel). Data oppdateres av appens
  egen scheduler.
- **MySpeed** (`.124:5216`, germannewsmaker) → `widget type: myspeed`
  (kaller `/api/speedtests?limit=1`).

`version: 1` for speedtest bruker v1-endepunktet som også LinuxServer-bildet svarer på uten
token (v2 `/api/v1/results/latest` er 302→login og krever `key:`). Hvis du senere setter et
passord på MySpeed, legg `password:` i widget-oppføringen.

## Deploy-merknad

Depotets `docker-compose.yml` MÅ vedlikeholdes likt det som kjører. En redeploy
spiller ut repo-et; hvis compose-en i repo-et avviker fra det deployede, endrer
en redeploy hvordan containerne kjører. Inkluderer `../homepage/config:/app/config:ro`
(directory-bind, ikke fil) og docker.sock — disse er påkrevd for GitOps + status.
