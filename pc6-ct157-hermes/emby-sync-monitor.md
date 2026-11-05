# Emby Download & Sync monitor

This Hermes component observes Emby's **Download & Sync** API on the primary
server (`10.0.0.150:8096`).  It is a read-only systemd timer; it does not
restart Emby, modify jobs, touch the library, or affect playback/transcoding.

## What it notifies

For a newly created Sync job it sends a Home Assistant notification with the
media title, Emby user, target device and current status. It sends a second
notification when a job completes or fails. The first run is only a baseline,
so an installation/restart never re-notifies about old jobs.

The state file is `/home/hermes/.hermes/data/emby_sync_state.json`. It contains
only job IDs, status, progress and target IDs. It never stores titles, user
names, API responses, media paths or API keys. Success runs are silent in the
system journal for the same reason.

The default target is the registered iPhone Home Assistant service. Set
`EMBY_SYNC_NOTIFY_TARGET` in Hermes' protected `.env` to change it after the
Mac/Windows Home Assistant clients register their own `notify` services.

## Important scope

This covers offline **Download & Sync** jobs, which Emby exposes through
`/Sync/Jobs` and `/Sync/JobItems`. A browser's ordinary direct file download
is not represented as a Sync job by Emby and therefore cannot be detected
reliably from this API. Job `Bitrate` is the requested output encoding rate,
not measured client transfer bandwidth; do not report it as network usage.

## Deployment and verification

Install the script as
`/home/hermes/.hermes/scripts/emby_sync_monitor.py`, the unit files under
`/etc/systemd/system/`, then run:

```sh
systemctl daemon-reload
systemctl enable --now emby-sync-monitor.timer
systemctl start emby-sync-monitor.service
systemctl status emby-sync-monitor.timer --no-pager
```

The first manual run establishes a baseline and intentionally sends no push.
The next actual Download & Sync action is the functional test. Use
`journalctl -u emby-sync-monitor.service` only for generic monitor errors;
the monitor intentionally omits media and user data from its logs.
