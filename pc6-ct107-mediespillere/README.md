# Media-spillere — pc6 CT107 (flyttet fra Unraid)

- **CT / node:** CT107 på pc6 (10.0.0.120)
- **LXC:** `pc6-ct107-mediespillere-gammel`
- **IP:** `10.0.0.160`
- **Mount:** Tower `Tower-media` → `/media` (read-only)
- **Status:** **stoppet, `onboot: 0` (autostart av)** — midlertidig mens tjenestene vurderes

## Tjenester (flyttet fra Unraid-Tower)

| Tjeneste | Type | Standard-port | Status |
|---|---|---|---|
| Plex | media-server | 32400 | kopiert og testet |
| Jellyfin | media-server | 8099 | data/konfig kopiert, ikke grundig testet (avventer bruker) |

## Bakgrunn

Begge tjenestene kjørte tidligere som Docker-containere i Unraid-VM-en
(`10.0.0.101`). Docker-pakkene ble kopiert ut og satt opp her i egen CT
siden Unraid-Docker er skrudd av. Ngrok var ikke aktuell (ingen appdata å
flytte). **Overseerr er slettet.**

Medieinnholdet ligger fortsatt på Tower og monteres lesbart på `/media`;
tjeneste-config/data ligger lokalt i CT-en. Autostart er bevisst av så CT-en
ikke kommer opp uregistrert etter en node-omstart.

## Start

```sh
pct start 107          # på pc6
# Plex:   http://10.0.0.160:32400/web
# Jellyfin: http://10.0.0.160:8099
```