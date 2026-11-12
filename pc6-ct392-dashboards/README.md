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
