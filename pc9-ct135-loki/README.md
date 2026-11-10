# pc9-ct135-loki

Sentral loggagring (Loki 3.5) for hjemmelaben.

- Node/CT: pc9 · CT135 · 10.0.0.211 · 2 kjerner, 2 GB RAM, 20 GB disk (laget med `ct-new`)
- Endepunkt: `http://10.0.0.211:3100` (`/ready`, `/loki/api/v1/push`)
- Retention: 30 dager (compactor), lagring på volumet `loki-data`
- Agent: Grafana Alloy sender hit (Promtail er avviklet). Alloy rulles ut per CT i egen endring.
- Visning: Grafana på CT109 (10.0.0.128:3000) → legg til datakilde Loki `http://10.0.0.211:3100`.
- Ingen autentisering; kun tilgjengelig på LAN.
