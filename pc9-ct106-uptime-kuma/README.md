# Uptime Kuma — PC9 secondary monitor

- **Status 26 October:** Existing runtime adopted in Komodo; service-only restart completed and all seven monitors verified UP.
- **Host:** PC9, existing `pc9-ct106-node`
  Periphery agent.
- **Runtime:** CT106 (`10.0.0.122`), separate Docker stack and database from
  Tunarr.
- **URL:** `http://10.0.0.122:3002`
- **Image:** `louislam/uptime-kuma:2.5.7` (pinned stable release)
- **Persistent data:** `/opt/komodo/stacks/pc9-ct106-uptime-kuma/data`

This is an independent *monitoring location* for PC6. It does not share the
primary Kuma SQLite database.

The installed monitors run every 60 seconds, with two retries and a 15-second
request timeout:

- Emby: `http://10.0.0.150:8096/web/`
- primary Uptime Kuma: `http://10.0.0.124:3001/`
- n8n health: `http://10.0.0.119:5678/healthz`
- Prometheus readiness (monitor 4): `http://10.0.0.126:9090/-/ready`
- Alertmanager readiness (monitor 6): `http://10.0.0.126:9093/-/ready`
- Blackbox exporter health (monitor 7): `http://10.0.0.126:9115/-/healthy`
- PC6 Proxmox web: `https://10.0.0.120:8006/` (self-signed TLS accepted)

## Verified adoption — 2026-10-26

- Komodo stack `pc9-ct106-uptime-kuma` uses server
  `6ab5f94f418a3f1c1b73ed95`, host directory
  `/opt/komodo/stacks/pc9-ct106-uptime-kuma`, `docker-compose.yml`, and
  existing project `uptime-kuma-pc9`. Existing bind data remains in `data/`.
- Online SQLite backup `kuma-before-adoption-2026-10-26T16-36-58-422Z.db`
  passes `PRAGMA integrity_check`. No new database or live SQL edits.
- Auto pull, update polling and auto update are explicitly disabled and read
  back from Komodo to prevent unintended runtime changes during adoption.
- Komodo update `6adf81aa4636d7b900f2b311` completed successfully:
  `docker compose -p uptime-kuma-pc9 restart uptime-kuma-pc9`.
  Tunarr remains started at `2026-10-26T12:10:44.207450167Z`; not restarted.
- Monitor 4's stored URL was corrected but its running check still used
  `.124:9090`. After Kuma-only restart, the corrected `.126` target is UP.
- Real Chromium Save on `/edit/4` emits `editMonitor` and receives a successful
  `Saved.` acknowledgement, with no page errors or visible invalid inputs.
  Blank required inputs belong to hidden setup dialogs. The earlier missing
  event is not reproducible after restart; no speculative application patch
  or authentication weakening was applied.
- At 16:48 UTC all seven monitors returned `200 - OK`, without duplicates.
  All seven are linked to existing notification ID 1,
  `PC9 Kuma → Home Assistant iPhone`. New monitors 6/7 use 60-second intervals,
  two retries and a 15-second timeout. No HA secret was copied into Git.
- This verifies the existing notification attachment, not a fresh end-to-end
  iPhone delivery test. No artificial production outage was induced.

## Direct iPhone alarms

PC9 Kuma now delivers outages directly to Home Assistant on PC8, which sends
the notification through `notify.mobile_app_1_iphone_r`. The notification is
enabled for all seven monitors above. This path does **not** depend on PC6 or
n8n:

`PC9 Kuma → Home Assistant (PC8) → iPhone`

The Home Assistant webhook identifier is an access secret. It exists only in
Home Assistant and the Kuma notification configuration; never put it in this
repository, a workflow export, screenshots, or logs.

This makes alerts resilient to a PC6/n8n outage. It cannot alert if PC9/CT106,
Home Assistant/PC8, or the LAN itself is unavailable; that would require an
external monitoring location or provider.

Manage the container through the Komodo stack `pc9-ct106-uptime-kuma`; do not
run ad-hoc `docker compose` commands in the stack directory.
