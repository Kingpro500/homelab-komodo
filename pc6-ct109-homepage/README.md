# Homepage — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-homepage`
- **Address:** `http://10.0.0.128:3009`
- **Config:** `homepage/config/` i repoet, mountet read-only

Hele konfigurasjonsmappa kommer fra Git:

```yaml
- ../homepage/config:/app/config:ro
```

Ingen Komodo-variabel trengs lenger. `HOMEPAGE_CONFIG_PATH=/opt/homepage` ligger
fortsatt i Stack Environment, men compose-fila bruker den ikke lenger.

## Mount hele mappa, ikke enkeltfilen

Dette er ikke en smakssak. Bind-mount av **en fil** går stale ved `git pull`:

- `git pull` bytter ut filen med en ny inode
- Mounten peker på den gamle inoden, så containeren fortsetter å lese gammelt innhold
- `docker compose up` gjenoppretter ikke containeren når compose-fila er uendret

Verifisert 4. oktober 2026: etter en redeploy med korrekt `deployed_hash` viste
klonen på verten 8 grupper og 49 tjenester, mens containeren serverte 7 grupper og
41. Containeren hadde startet timer tidligere. Fiksen er å mounte **mappen**; da
følger mounten nye filer fordi katalogen, ikke inoden, er det som er bundet.

## Endre tjenestelisten

1. Endre `homepage/config/services.yaml` og push.
2. Redeploy `pc6-ct109-homepage` i Komodo.
3. Kontroller: `curl -s http://10.0.0.128:3009/api/services | grep -c href`

Komodos `file_paths` er `['docker-compose.yml']`. Det er riktig: `file_paths`
er for **ekstra compose-filer** (`docker compose -f … -f …`), ikke for datafiler.
Konfigurasjonsfilene hentes av `git pull` under deploy, ikke av `file_paths`.

Strukturen i `services.yaml` er `icon` / `href` / `description` per oppføring, med
4 mellomrom for oppføring og 8 for feltene. `icon: noen.png` slår opp i
`/opt/homepage/icons/` og gir en ødelagt flis; bruk `si:`, `sh:`, `di:` eller
`mdi:` for ikoner som hentes fra et CDN.

### Widgets

En oppføring kan ha et `widget:`-nivå på 8 mellomrom, under `description`:

```yaml
    - Uptime Kuma:
        icon: uptime-kuma.png
        href: http://10.0.0.128:3001/
        description: 10.0.0.128:3001 · CT109 · pc6
        widget:
          type: uptimekuma
          url: http://10.0.0.128:3001
          version: 1
```

Uptime Kuma-widgeten snakker **socket.io**, ikke REST. Verifisert 4. oktober
2026 på `10.0.0.128:3001`:

- `GET /socket.io/?EIO=4&transport=polling` svarer `200` med en gyldig handshake
- `GET /api/status/heartbeat` og `/api/status/up` returnerer **HTML**, ikke JSON —
  de er ikke widgetens vei
- `GET /api/status-page/heartbeat/default` svarer JSON, men `heartbeatList` var
  tom, så ingen statuspage er satt opp

Det betyr widgeten virker teknisk, men viser ingenting før det finnes en
statuspage med monitorer i Uptime Kuma. REST-endepunktene som ser «ut til å
svare» med HTTP 200 er SPA-fallback, ikke bevis på at widgeten har data.

## /opt/homepage

Den gamle runtime-katalogen ligger fortsatt på CT109 og brukes ikke lenger. Den
inneholder kun `custom.css` og `custom.js` (begge tomme) samt noen
`services.yaml.bak-*` fra tidligere kopieringer. Kan slettes, men er ikke
undersøkt — ingen sletting gjort av automatisering.

## Relatert

- `homepage/config/services.yaml` — tjenestelisten
- `tools/seed-heimdall.js` — speiler samme liste inn i Heimdall
- `migration-backlog.md` — oppføringen «Homepage»