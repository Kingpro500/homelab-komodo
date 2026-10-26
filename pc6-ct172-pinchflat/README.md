# Dedicated Pinchflat on pc6 CT172

This stack runs Pinchflat on `pc6-ct172-pinchflat` at `10.0.0.164`.

- Pinchflat configuration and SQLite data live locally at `/opt/pinchflat`.
- Tower media is mounted by Proxmox at `/media`; only `/media/YouTube` is passed to the container.
- `YT_DLP_WORKER_CONCURRENCY=1` prevents the parallel yt-dlp/deno burst that exhausted RAM, swap, and NFS I/O on CT120.
- The image is pinned by digest and excluded from automatic Watchtower upgrades.
- The old Pinchflat container on CT120 remains stopped as rollback until this stack is verified.

Komodo variables:

```dotenv
PINCHFLAT_CONFIG_PATH=/opt/pinchflat
TOWER_MEDIA_PATH=/media
TZ=Europe/Oslo
```

Before deploy, verify that `/media/YouTube` is mounted and writable. Deploy only through Komodo.
