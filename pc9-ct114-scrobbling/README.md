# pc9-ct114-scrobbling

Koito + multi-scrobbler i CT114 (`pc9-ct114-navidrome`, 10.0.0.172), ved siden av Navidrome.

| Tjeneste | URL | Rolle |
| --- | --- | --- |
| Koito | http://10.0.0.172:4110 | Lagrer og viser lyttehistorikk (SQLite i `/opt/scrobbling/koito`). ListenBrainz-API: `http://10.0.0.172:4110/apis/listenbrainz/1` |
| multi-scrobbler | http://10.0.0.172:9078 | Henter avspillinger fra kilder og sender dem til Koito |

## Hemmeligheter

Står i Komodo-stackens **Environment**, aldri i git:

- `KOITO_DEFAULT_PASSWORD` – passord for Koito-brukeren `roger` (gjelder bare første oppstart; endres senere i Koito).
- `KOITO_TOKEN` – API-nøkkel fra Koito (Innstillinger → API Keys). multi-scrobbler bruker den for å sende scrobbles.

## Kilder

- **Web Scrobbler** (nettleserutvidelse, dekker Qobuz/YouTube Music i nettleser): Accounts → Webhook → API URL `http://10.0.0.172:9078/api/webscrobbler`.
- **Navidrome**: kan sende direkte til Koito via ListenBrainz (`ND_LISTENBRAINZ_BASEURL=http://10.0.0.172:4110/apis/listenbrainz/1/`), eller via multi-scrobbler (`SUBSONIC_*`).
- **Spotify** (`SPOTIFY_CLIENT_ID/SECRET`): krever HTTPS- eller 127.0.0.1-redirect, se multi-scrobbler-dokumentasjonen.

Data: `/opt/scrobbling/koito` (Koito) og `/opt/scrobbling/multi-scrobbler/config` (eies av 1000:1000).
