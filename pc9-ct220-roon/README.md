# Roon Server — pc6 CT 152

- **CT:** 152 on pc6
- **Address:** `10.0.0.125`
- **Network:** host mode inside its dedicated LXC so Roon LAN discovery and multicast work normally.
- **Music:** mounted from Tower at `/music` as read-only; media is never copied into this CT.
- **Roon app state:** `/opt/roon/app` and `/opt/roon/data` in the CT.
- **Backups:** Tower's existing Roon backup folder is mounted at `/backup` read-write.

Komodo variables required: `ROON_APP_PATH`, `ROON_DATA_PATH`, `ROON_MUSIC_PATH`, `ROON_BACKUP_PATH`, and `TZ`.
