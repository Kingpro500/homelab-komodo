# Prometheus — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-prometheus`
- **UI:** `http://10.0.0.128:9090`

Prometheus is the bridge between an exporter and Grafana. Netdata cannot feed
Grafana: its Grafana plugin is gone from the registry, and its
`/api/v1/allmetrics` endpoint is an *export* endpoint that Prometheus rejects
(parse error `="NN"` in every Prometheus version). Netdata is therefore not usable
as a Grafana source.

Instead Prometheus scrapes an **exporter we control** that serves clean
Prometheus-format metrics:

| job | what | URL Prometheus scrapes |
|---|---|---|
| `homelab-resources` | per-guest CPU/RAM/disk from Proxmox (read-only API) | `http://10.0.0.135:9120/metrics` |

The exporter (`homelab_metrics_exporter.py` on CT157, systemd unit
`homelab-metrics.service`) polls Proxmox `/status/current` per guest and exposes
`proxmox_guest_*` gauges:

```promql
proxmox_guest_mem_used_bytes{node=~"$node"}
proxmox_guest_cpu_percent{node=~"$node"}
proxmox_guest_disk_used_bytes{node=~"$node"}
```

Chain: Proxmox → exporter (CT157:9120) → Prometheus (CT109:9090) → Grafana
(`pc6-ct109-grafana`, datasource `uid=prometheus`, default). Prometheus keeps 30
days in the named volume `prometheus-data`.

## Grafana side

Grafana has a provisioned Prometheus datasource pointing at `http://10.0.0.128:9090`
and a dashboard under `pc6-ct109-grafana/provisioning/dashboards/homelab-overview.json`.
NB: Grafana 13.x does not auto-load the legacy file-based dashboard provisioning;
the dashboard JSON must be imported via API/UI (it is version-controlled in this
repo under `pc6-ct109-grafana/`).

## Notes

- Light footprint by design: 30s scrape interval, ~50 MB RAM idle.
- CT109 is already loaded; the whole metrics stack can move to a less loaded guest
  if it ever matters.