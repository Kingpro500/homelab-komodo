# PC9 observability

Komodo-managed Prometheus, Alertmanager and Blackbox exporter on CT104
(`10.0.0.126`). This is intentionally independent of PC6.

Git is the stack source; deploy only through the Komodo stack
`pc9-ct104-observability`. PC9 Uptime Kuma remains the direct Home Assistant /
iPhone availability-alert path when PC6 or n8n is unavailable.

Network-interface monitoring is documented in `docs/network-interface-monitoring.md`.
The `network-interface` Prometheus job scrapes the read-only exporter at
`10.0.0.135:9122/metrics` and alerts on link-down and sustained RX drops.

The exporter now runs as `network-interface-exporter` inside this same CT104
Komodo stack and reads only `/sys/class/net/*` counters and carrier state.
