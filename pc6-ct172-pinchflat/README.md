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

## yt-dlp base config (YouTube 429 on subtitles)

Since mid-November 2026 YouTube answers many subtitle requests with
`HTTP Error 429: Too Many Requests`. By default yt-dlp then fails the whole
video, so Pinchflat stopped downloading (584 items stuck on 18 Nov 2026).

The fix lives in Pinchflat's own yt-dlp config, which Pinchflat passes with
`--config-locations` on every call:

- Live file: CT172 `/opt/pinchflat/extras/yt-dlp-configs/base-config.txt`
- Versioned copy: [`yt-dlp-base-config.txt`](yt-dlp-base-config.txt) — keep both identical.

`--ignore-errors` turns a failed subtitle into a warning (the video is still
saved, the missing language is skipped); real download failures still exit
non-zero and are retried by Pinchflat. `--sleep-subtitles`/`--sleep-requests`
pace requests to lower the 429 rate. Check with:

```bash
pct exec 172 -- docker logs --since 1h pinchflat 2>&1 | grep -c "HTTP Error 429"
```
