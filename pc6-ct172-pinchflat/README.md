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

## YouTube cookies (bot check "Sign in to confirm you're not a bot")

- File: CT172 `/opt/pinchflat/extras/cookies.txt` (mode 600, never committed or displayed).
  Copied on 18 Nov 2026 from the MeTube export on CT120 `/opt/metube/Cookies/cookies.txt`
  (exported 8 Aug 2026). Renew both from the same browser export when they stop working.
- All sources use cookie behaviour `when_needed` (set 18 Nov 2026; previously `disabled`).
  Pinchflat 2025.9.26 then uses cookies for indexing and for error recovery: a download that
  fails with "Sign in to confirm" is retried with cookies. Ordinary downloads run without the
  account, which limits the risk of YouTube flagging it. New sources must also be set to
  "When needed" in the UI.
- Check that the login is still valid without listing account data:

```bash
pct exec 172 -- docker exec pinchflat yt-dlp --cookies /config/extras/cookies.txt --flat-playlist -I 1:3 --print id ":ytsubs" | wc -l
```

  Note: yt-dlp may rewrite the cookie file it is given; test against a copy if in doubt.

## Recovery: downloads stalled in retry backoff

Oban retries failed downloads with exponential backoff (up to 20 attempts). After a
burst of failures (e.g. the 429 period), every pending job can end up waiting hours or
days, so nothing downloads even though the cause is fixed. Seen 19 Nov 2026: all 196
pending download jobs were `retryable` on attempt 18–19 and only 1 was `available`.

Check (read-only):

```bash
pct exec 172 -- python3 -c "import sqlite3;c=sqlite3.connect('file:/opt/pinchflat/db/pinchflat.db?mode=ro',uri=True);print(c.execute(\"select state,count(*),min(scheduled_at) from oban_jobs where worker='Pinchflat.Downloading.MediaDownloadWorker' and state in ('available','retryable','executing') group by 1\").fetchall())"
```

Fix (same effect as `Oban.retry_job/1`; save the rows first): set those jobs to
`state='available'`, `scheduled_at=now`, `max_attempts=max(max_attempts, attempt+5)`.
The 19 Nov backup of the rows is `/opt/pinchflat/db/oban-retryable-backup-20261119.json`.
