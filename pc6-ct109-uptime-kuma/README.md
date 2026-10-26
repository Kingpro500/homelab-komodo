# Uptime Kuma — PC6 CT120

- **Runtime CT:** PC6 / CT120 (renumbered from the former CT109).
- **Address:** `http://10.0.0.124:3001`
- **Runtime data:** `/opt/uptime-kuma/data/kuma.db`
- **Deployment status:** legacy runtime on CT120. Treat the running Kuma UI and
  its database as the source of truth until it has been deliberately imported
  into a Komodo-managed stack.

## Critical notification route

Uptime Kuma uses the notification **`Kritisk homelab → iPhone via n8n`**. It
sends a token-free, internal-LAN webhook to n8n at
`http://10.0.0.119:5678/webhook/homelab-alerts`; n8n then uses its existing
Home Assistant credential to notify the iPhone and log the event. No Home
Assistant token is stored in this repository or duplicated in Kuma.

Attached critical monitors use a 60-second interval, a 30-second retry interval
and two retries. They cover Emby, both Tunarr M3U feeds, Roon, Unraid, the four
Proxmox nodes, OPNsense, Komodo, n8n, Hermes, Prometheus and Kuma itself.

The health endpoints that matter are checked rather than only a web front page:

- Emby: `http://10.0.0.150:8096/web/`
- Tunarr PC6: `http://10.0.0.123:8005/api/channels.m3u`
- Tunarr PC9: `http://10.0.0.122:8005/api/channels.m3u`
- n8n: `http://10.0.0.119:5678/healthz`
- Prometheus now lives on PC9 CT104: `http://10.0.0.126:9090/-/ready`.
  The list above describes the legacy primary configuration; its stored monitor
  target must be checked separately, not inferred from this documentation.

The independent PC9 Kuma at `http://10.0.0.122:3002/` is now Komodo-managed
and checks Prometheus, Alertmanager and Blackbox on `.126` with its existing
direct Home Assistant notification, independently of the primary Kuma/n8n.
See [PC9 runtime and verification](../pc9-ct106-uptime-kuma/README.md).

Kuma sends a down event only after its retry policy is exhausted and a recovery
event when the service returns. Do not attach the notification to every
best-effort monitor: that would turn the iPhone alert stream into noise.

## Safe changes and recovery

Never edit `kuma.db` while Uptime Kuma is running. Prefer the Kuma UI. If an
emergency database migration is unavoidable, stop only `uptime-kuma`, create a
timestamped copy of `kuma.db`, make one transactional change, run
`PRAGMA integrity_check`, then start Kuma and verify every affected monitor.

The notification route depends on both n8n and Home Assistant. It therefore
cannot alert the iPhone if either of those is unavailable. Keep the independent
Prometheus/Alertmanager path, and add an external notification provider before
calling the alerting design fully fault-tolerant.
