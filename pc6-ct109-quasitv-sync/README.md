# QuasiTVSync — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-quasitv-sync`
- **Admin UI:** `http://10.0.0.128:26988`
- **Sync port:** `10.0.0.128:51234`

## What this is, and what it is not

QuasiTV is an **Android / Google TV app** from the Play Store — it is not
self-hosted and does not run in Docker. This stack is QuasiTVSync, the separate
self-hosted backend that syncs profiles, channel lineups and schedules across
the TVs in the house.

**The server is useless without QuasiTV Ultimate.** Upstream says so in its own
README: "Requires QuasiTV Ultimate In App Purchase". This is a paid in-app
purchase, so buy the app on the TV before spending time on the setup.

The TV apps are what actually play anything. The server only keeps their state
in agreement.

## Why it lives here rather than next to Emby

It does not need to be near Emby — it talks to it over HTTP. Emby stays on CT151
(`pc6-ct151-emby`, `http://10.0.0.150:8096`, "Tower Emby" 4.10.0.40) and
QuasiTVSync on CT109 is pointed at that address during setup. Same node as the
other dashboards, so it lands where the rest of the stack config lives.

## Setup

1. Open `http://10.0.0.128:26988`.
2. Create a username and password. This is the server's own account — it is not
   the Emby one, and it never leaves this box.
3. Choose content server type **Emby**.
4. Point it at `http://10.0.0.150:8096` and sign in with Emby credentials.
5. In the QuasiTV app on each TV, enter `10.0.0.128` and port `51234`.

## Volumes and permissions

State lives in two named volumes, `quasitv-settings` and `quasitv-data`. Upstream
asks for bind mounts plus `chmod 755` on the host directories; named volumes
avoid that, because the image applies `PUID`/`PGID` to them itself. Both need
read-write access, which they have.

## No platform flag

Upstream mentions `--platform=linux/amd64` for non-x86 hosts. CT109 is x86_64, so
it is unnecessary here.