# Media recovery and version audit

This runner is invoked only through the restricted media-recovery SSH key. It performs bounded NFS, media-read and Tunarr API/web checks. The Tunarr check deliberately does not open an HLS stream: doing so started an ffmpeg transcode on every 5-minute probe that never went idle (fixed 2026-11-08). Its recovery boundary excludes Emby: Emby is observation-only; only Tunarr recovery is allowlisted.

The JSON report includes `installed_images` for Emby and both separate Tunarr instances. n8n consumes that field for a daily version audit. The runner does **not** contact registries, update images or restart Emby.

Exception (2026-11-22): `emby_backup_watch()` checks Emby CT200's config-backup mount and, if stale, re-binds `/var/lib/emby-backups` inside CT200's mount namespace and re-runs a missed backup. It never restarts Emby or touches the media mounts the Emby container uses. The result is `services["emby-backup"]`; see `pc6-ct200-emby/README.md`.

Deploy source through the controlled PC6 media-recovery procedure. Do not run Docker commands manually.
