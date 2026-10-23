# Uptime Kuma — PC9 secondary monitor

- **Host:** PC9, deployed through Komodo on the existing `pc9-ct106-node`
  Periphery agent.
- **Runtime:** CT106 (`10.0.0.122`), separate Docker stack and database from
  Tunarr.
- **URL:** `http://10.0.0.122:3002`
- **Persistent data:** `/opt/komodo/stacks/pc9-ct106-uptime-kuma/data`

This is an independent *monitoring location* for PC6. It does not share the
primary Kuma SQLite database.

The installed monitors run every 60 seconds, with two retries and a 15-second
request timeout:

- Emby: `http://10.0.0.150:8096/web/`
- primary Uptime Kuma: `http://10.0.0.124:3001/`
- n8n health: `http://10.0.0.119:5678/healthz`
- Prometheus health: `http://10.0.0.124:9090/-/healthy`
- PC6 Proxmox web: `https://10.0.0.120:8006/` (self-signed TLS accepted)

## Direct iPhone alarms

PC9 Kuma now delivers outages directly to Home Assistant on PC8, which sends
the notification through `notify.mobile_app_1_iphone_r`. The notification is
enabled for all five monitors above. This path does **not** depend on PC6 or
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
