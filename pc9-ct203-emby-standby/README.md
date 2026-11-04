# PC9 CT203 — Emby warm standby

This is the independent Emby standby on **PC9 / CT203 / 10.0.0.127:8096**.

## Safety model

- It uses the same Tower media tree as CT200, mounted at `/mnt` in Emby and read-only.
- It has a **separate** `/opt/emby/EmbyServer` config and SQLite database.
  Never bind-mount, rsync, or otherwise share CT200's live `/config` while both servers run.
- It uses PC9's Intel Quick Sync device `/dev/dri/renderD128`.
- A client cannot seamlessly migrate an existing Emby/HLS session. During a planned
  primary change, reconnect to the standby server; it can stream the same media
  independently once its libraries are configured.
- Do not enable unattended image updates for this stack. Use it as the canary:
  test the target stable `4.10.x` image here, then explicitly promote CT200.

## Deployment

Komodo Core manages this stack through the `pc9-ct203-emby-standby` server.
Application deployment is only through Komodo. Docker/Compose in CT203 is the
one-time host bootstrap for Komodo Periphery.

## Recovery limits

Tower/NFS remains a shared dependency: a Tower or NFS outage affects both Emby
servers. This standby protects a planned or unplanned failure of CT200/PC6, not
the media-storage dependency.
