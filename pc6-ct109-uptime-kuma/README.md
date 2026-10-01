# Uptime Kuma — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-uptime-kuma`
- **Address:** `http://10.0.0.128:3001`
- **Runtime data:** `/opt/uptime-kuma/data`

Tower's former Kuma database is copied once as migration data. The Tower copy is
kept untouched for rollback. Required Komodo variable:
`UPTIME_KUMA_DATA_PATH=/opt/uptime-kuma/data`.
