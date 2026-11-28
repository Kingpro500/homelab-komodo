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
- `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` – Spotify-appen «multi-scrobbler» (developer.spotify.com, redirect `http://127.0.0.1:9078/callback`). Tokenet lagres i `/opt/scrobbling/multi-scrobbler/config` etter godkjenning.

## Kilder

- **Sonos** (kilde `sonos`): lokal Sonos-API via Arc på 10.0.0.15 (`SONOS_HOST`). Dekker alt som spilles på Sonos (alle soner).
- **Web Scrobbler** (nettleserutvidelse, dekker Qobuz/YouTube Music i nettleser): Accounts → Webhook → API URL `http://10.0.0.172:9078/api/webscrobbler`.
- **Navidrome**: scrobbler direkte til Koito via ListenBrainz-API (`ND_LISTENBRAINZ_BASEURL` i `pc9-ct114-navidrome`). Kobles per bruker i Navidrome: Personal → ListenBrainz → lim inn `KOITO_TOKEN`.
- **Spotify** (kilde `spotify`): godkjennes i dashbordet; nettleseren havner på `127.0.0.1:9078/callback?code=…` – bytt `127.0.0.1` med `10.0.0.172` og trykk Enter.
- Last.fm brukes ikke som kilde (API-nøkler krever Pro fra 1. des 2026, og Sonos + Spotify dekker det samme). Gammel historikk importeres i Koito fra eksport.

Data: `/opt/scrobbling/koito` (Koito) og `/opt/scrobbling/multi-scrobbler/config` (eies av 1000:1000).

## Kjent felle

`/music` i CT114 er en NFS-mount fra Unraid (mp0). Får Navidrome «mkdir /music: file exists» ved deploy, er handlet stale (`ls /music` → «Stale file handle»). Hot-replug av mp0 hjelper ikke; `pct reboot 114` gjør. Flytt eventuelle Koito-importfiler ut av `import/` først, ellers starter importen på nytt.
