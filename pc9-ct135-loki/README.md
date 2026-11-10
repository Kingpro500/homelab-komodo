# pc9-ct135-loki – sentral loggagring (VictoriaLogs)

CT135 på pc9, 10.0.0.211. Kjører VictoriaLogs (port 9428, 30 dagers retention).
Stack-/mappenavnet «loki» er historisk (byttet fra Loki til VictoriaLogs) og beholdes for å matche Komodo-serveren.

- UI: http://10.0.0.211:9428/select/vmui
- Helse: http://10.0.0.211:9428/health
- Loki-kompatibel push: http://10.0.0.211:9428/insert/loki/api/v1/push (Alloy `loki.write`)
- Grafana: VictoriaLogs-datakilde-plugin (victoriametrics-logs-datasource)
