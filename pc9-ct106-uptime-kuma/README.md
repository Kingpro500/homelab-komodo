# Uptime Kuma — PC9 secondary monitor

- **Host:** PC9, deployed through Komodo on the existing `pc9-ct106-node`
  Periphery agent.
- **Runtime:** CT106 (`10.0.0.122`), separate Docker stack and database from
  Tunarr.
- **URL:** `http://10.0.0.122:3002`
- **Persistent data:** `/opt/komodo/stacks/pc9-ct106-uptime-kuma/data`

This is an independent *monitoring location* for PC6. It must monitor the
PC6-critical endpoints (Emby, primary Kuma, n8n, Prometheus and the PC6
Proxmox host) at a short interval. It does not share the primary Kuma SQLite
database.

The iPhone notification currently passes through n8n on PC6. Therefore this
secondary Kuma can detect a PC6 outage, but cannot deliver an iPhone alert
while PC6/n8n is unavailable. A direct PC9-to-Home-Assistant or external
notification route is needed before it becomes independent alerting as well.

Manage the container through the Komodo stack `pc9-ct106-uptime-kuma`; do not
run ad-hoc `docker compose` commands in the stack directory.
