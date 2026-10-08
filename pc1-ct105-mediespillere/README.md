# Media players on PC1 CT105

This temporary, manually-started CT runs the former Tower containers
`binhex-plex` and `binhex-jellyfin`.

- **Host / CT:** pc1 / CT105 (`pc1-ct105-mediespillere`)
- **IP:** `10.0.0.159`
- **Plex:** `http://10.0.0.159:32400/web`
- **Jellyfin:** `http://10.0.0.159:8099`
- **Persistent configuration:** `/opt/media-players` in the CT
- **Media:** Tower NFS bind at `/media`, mounted read-only

The CT has `onboot: 0` and is intentionally shut down after its migration
test. Start CT105 manually when these players are needed; Docker will then
start both services automatically.
