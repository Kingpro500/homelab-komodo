# Prometheus — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-prometheus`
- **UI:** `http://10.0.0.128:9090`

Prometheus bridges Netdata into Grafana. Netdata cannot be queried by Grafana
directly: its Grafana plugin is gone from the registry, and its
`/api/v1/allmetrics` endpoint is an *export* endpoint (Prometheus scrapes it), not
a PromQL query API — so a Grafana `prometheus`-type datasource pointed at Netdata
returns 404 on every query.

This stack scrapes the four Netdata nodes via their Prometheus export endpoint and
exposes a real PromQL API that Grafana can query:

| target | URL Prometheus scrapes |
|---|---|
| Tower | `http://10.0.0.101:19999/api/v1/allmetrics` |
| pc6 | `http://10.0.0.120:19999/api/v1/allmetrics` |
| pve | `http://10.0.0.102:19999/api/v1/allmetrics` |
| pc9 | `http://10.0.0.103:19999/api/v1/allmetrics` |

Network: Netdata → Prometheus (scrape) → Grafana (query). Prometheus keeps 30
days in the named volume `prometheus-data`.

## Grafana side

Grafana (`pc6-ct109-grafana`) has a provisioning file that declares a Prometheus
datasource pointing at `http://10.0.0.128:9090`. After this stack is up and
scraping, panels in Grafana can query metrics such as:

```promql
netdata_system_ram_MiB_average{dimension="used", instance="10.0.0.120:19999"}
netdata_disk_space_GiB_average{dimension="used"}
netdata_system_load_load_average{dimension="load1"}
```

## Notes

- Light footprint by design: 30s scrape interval, ~50 MB RAM idle.
- CT109 is already loaded (many containers); Prometheus is small but it is
  another always-on process here. If it ever matters, the whole metrics stack can
  move to a less loaded guest.