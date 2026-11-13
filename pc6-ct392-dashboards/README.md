# Dashboards — pc6 CT154 (10.0.0.166)

| | |
|---|---|
| **Proxmox-CT** | CT154 `pc6-ct154-dashboards` på pc6. Lå i CT392 fram til 13.11.2026 |
| **Komodo-server** | `pc6-ct392-dashboards` (navnet lyver, se nederst. Agent: systemd, `connect_as` i `/etc/komodo/periphery.config.toml`) |
| **Komodo-stack** | `pc6-ct392-dashboards`, `project_name = dashboards` |
| **Compose-prosjekt på verten** | `dashboards` |

## Hva kjører

| Tjeneste | Adresse | Status |
|---|---|---|
| Grafana | http://10.0.0.166:3000 | kjører |
| Glance | http://10.0.0.166:3010 | på pause |
| Dashy | http://10.0.0.166:3011 | på pause |
| Heimdall | http://10.0.0.166:3012 | på pause |

De tre siste står under compose-profilen `pause`, så `docker compose up -d`
og Komodos Deploy starter dem ikke. Skal én av dem opp igjen, må brukeren si
det — se punkt 9 i [AGENTS.md](../AGENTS.md) om Homepage og Dashy.

## Historikk — hvorfor navnene er som de er

Tjenestene lå i CT109 (senere renummerert til CT210) og ble flyttet til CT392
11. nov 2026. Komodo fulgte ikke med: de fire stackene `pc6-ct109-grafana`,
`-dashy`, `-glance` og `-heimdall` sto igjen på serveren `pc6-ct109-node`
(= CT210) med status *down*, mens Grafana kjørte i CT392 helt utenfor Komodo.
Mappene `pc6-ct109-{dashy,glance,grafana,heimdall}/` i dette repoet er
erstattet av denne, og de fire gamle stackene er slettet i Komodo.

Datamappene på verten heter fortsatt `pc6-ct109-*_*-data`, fordi det var
navnene på de gamle Docker-volumene. De er bare mapper nå, og skal ikke
døpes om — da mister Dashy og Heimdall innstillingene sine.

## Tilstand på verten

| Sti | Innhold |
|---|---|
| `/opt/grafana/data` | Grafanas database (`grafana.db`) |
| `/opt/dashboards/volumes/pc6-ct109-dashy_dashy-data/_data` | Dashys `conf.yml`, redigeres fra Dashys eget nettgrensesnitt |
| `/opt/dashboards/volumes/pc6-ct109-heimdall_heimdall-data/_data` | Heimdalls SQLite-base og app-nøkkel |

`/opt/dashboards/docker-compose.yml` på verten er filen fra flyttingen og
brukes ikke lenger — Komodo kjører fra sin egen klone av dette repoet.

## Komodo-variabler

```
GRAFANA_DATA_PATH=/opt/grafana/data
GRAFANA_ROOT_URL=http://10.0.0.166:3000
DASHY_DATA_PATH=/opt/dashboards/volumes/pc6-ct109-dashy_dashy-data/_data
HEIMDALL_DATA_PATH=/opt/dashboards/volumes/pc6-ct109-heimdall_heimdall-data/_data
TZ=Europe/Oslo
```

## Filer herfra

- `provisioning/` — Grafanas datakilder og dashbord (flyttet fra `pc6-ct109-grafana/`)
- `glance.yml` — Glance-konfigurasjonen, med adressene oppdatert til 10.0.0.166
- `dashy-config/conf.yml` — referansekonfigurasjon for Dashy, ikke i bruk av
  den kjørende tjenesten (Dashy lagrer sin egen i datamappen). Lå før i
  `pc6-ct109-dashy/config/conf.yml` og inneholder den umergede endringen fra
  PR #78 som står på pause.

## To innstillinger som må bli stående

**`ignore_services = ["dashy","glance","heimdall"]`** på Komodo-stacken.
Komodo leser alle fire tjenestene ut av compose-filen når den regner ut
status, også de som ligger under profilen `pause`. Uten denne listen står
stacken som *unhealthy* fordi tre containere er stoppet, og drift-vakten
melder falsk alarm. Med listen står den som *running*.

**`legacy_compose_cli = false`** i `/etc/komodo/periphery.config.toml` i CT154.
CT154 er Debian 13 (trixie) med husstandarden docker.io 26.1.5 og
`docker compose` 2.x, så flagget skal være **av**. I CT392 måtte det stå på
`true`, fordi den hadde Docker 20.10.24 og bare `docker-compose` 1.29.2 —
uten flagget kjørte Periphery `docker compose` og deployen feilet med
*unknown shorthand flag*. Den gjelden er gjort opp med flyttingen.

## 13. november 2026 — flyttet fra CT392 til CT154

Grafana, de 729 MB med data i `/opt/grafana` og mappen `/opt/dashboards` ble
flyttet til CT154, som er fersk Debian 13. Alle 1303 filer ble sammenliknet
med `md5sum` på begge sider og var identiske før CT392 ble slått av.

| | CT392 (før) | CT154 (nå) |
|---|---|---|
| OS | Debian 12 bookworm | Debian 13 trixie |
| Docker | 20.10.24 | 26.1.5 |
| Compose | `docker-compose` 1.29.2 | `docker compose` 2.x |
| `legacy_compose_cli` | `true` | `false` |
| IP | 10.0.0.166 | 10.0.0.166 (overtatt) |
| Ressurser | 2 kjerner / 2 GB / 24 GB | 2 kjerner / 2 GB / 16 GB |

**CT392 står igjen urørt som angrefrist.** Slått av, `onboot: 0`, og IP-en
flyttet til 10.0.0.231 så den aldri kolliderer med CT154 om noen starter den.
Den har fortsatt dødt gods som ikke ble med: `/opt/open-webui` (890 MB) og
`/opt/diskspeed` (diskspeed kjører i CT120). Slett ikke CT392 uten at Roger
sier det.

**Navnegjeld:** Komodo-serveren, Komodo-stacken og denne mappen heter fortsatt
`pc6-ct392-dashboards` selv om tjenesten bor i CT154. Periphery i CT154 kobler
seg på med `connect_as = "pc6-ct392-dashboards"` og bruker nøklene fra CT392,
nettopp for at Komodo ikke skulle merke flyttingen. Navnebyttet er en egen jobb
som må tas i Komodo, GitHub og kartet samtidig — ikke rydd i det halvveis.
