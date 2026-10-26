# PC9 observability

Komodo-managed Prometheus, Alertmanager and Blackbox exporter on CT104
(`10.0.0.126`). This is intentionally independent of PC6.

Git is the stack source; deploy only through the Komodo stack
`pc9-ct104-observability`. PC9 Uptime Kuma remains the direct Home Assistant /
iPhone availability-alert path when PC6 or n8n is unavailable.
