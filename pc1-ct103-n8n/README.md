# n8n on pc1 CT 103

- **Host:** pc1 (`10.0.0.112`)
- **LXC:** `pc1-ct103-node`
- **IP:** `10.0.0.119`
- **URL:** `http://10.0.0.119:5678`

The stack uses a dedicated PostgreSQL 16 database. Its application state and
database are stored only in `/opt/n8n` inside the LXC; values for the database
password and n8n encryption key are Komodo secret variables and never belong
in Git.

## pc1 workload profile

This is the active lightweight automation profile for pc1. Ollama remains in
CT 156 with autostart disabled while CT 103 is active. Before switching back to
Ollama, stop the `pc1-ct103-n8n` stack in Komodo and stop CT 103; then start CT
156 and deploy or start `pc1-ct156-ollama` through Komodo.
