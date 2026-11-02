# PC9 observability

Komodo-managed Prometheus, Alertmanager and Blackbox exporter on CT104
(`10.0.0.126`). This is intentionally independent of PC6.

The stack also builds a local, dependency-free network-interface exporter. It
reads CT104's `eth0` counters from a read-only `/sys/class/net` mount and exposes
them to Prometheus as `network_interface_*` metrics. The exporter is internal to
the Compose network and is not published on the LAN.

Git is the stack source; deploy only through the Komodo stack
`pc9-ct104-observability`. PC9 Uptime Kuma remains the direct Home Assistant /
iPhone availability-alert path when PC6 or n8n is unavailable.
