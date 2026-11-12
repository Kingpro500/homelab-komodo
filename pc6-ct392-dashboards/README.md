# Dashboards — pc6 CT392 (10.0.0.166)

| | |
|---|---|
| **Komodo-server** | `pc6-ct392-dashboards` (agent: systemd, `connect_as` i `/etc/komodo/periphery.config.toml`) |
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

**`legacy_compose_cli = true`** i `/etc/komodo/periphery.config.toml` i CT392.
CT392 har Docker 20.10.24 og bare `docker-compose` 1.29.2 — ikke
compose-v2-tillegget (`docker compose`) som resten av homelab-et bruker.
Uten flagget kjører Periphery `docker compose` og deployen feiler med
*unknown shorthand flag*. Profiler virker i 1.29.2, det er testet i CT392.
Gammel kopi: `periphery.config.toml.bak-20261112`.

> **Gjeld:** CT392 (og CT210) står på Debian 11-utgaven av Docker selv om
> systemet er Debian 12, og apt-kildene har ikke `docker-compose-v2`. Skal de
> opp på husstandarden (docker.io 26.1.5 + docker-compose-v2 2.26.1, som CT120
> og CT172), må apt-kildene fikses først, og da restarter Docker-motoren og
> containerne. Ikke gjort 12. nov 2026.
