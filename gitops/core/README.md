# Komodo Core — pc8 CT110 (/opt/komodo)

This directory mirrors the production Compose layout on CT110 without storing
credentials. Production uses project name `komodo` and these two files:

- `/opt/komodo/ferretdb.compose.yaml`
- `/opt/komodo/compose.performance.yaml`

The real `/opt/komodo/compose.env` stays on CT110 and must never be committed.
Create it from `compose.env.example` for a new installation.

## Validate safely

Run on CT110:

```bash
cd /opt/komodo
docker compose \
  -p komodo \
  --env-file compose.env \
  -f ferretdb.compose.yaml \
  -f compose.performance.yaml \
  config --quiet
```

Do not deploy this stack automatically from Komodo Core itself. Before a
manual deployment, create both a Komodo database backup and a Proxmox backup
of CT110, then review the rendered config and image changes.

## Current database generation

Production uses FerretDB v2 with `ghcr.io/ferretdb/postgres-documentdb`. Do not
replace it with the previous `postgres:16-alpine` / FerretDB v1 layout. A v1 to
v2 database transition is a migration, not an in-place image update.
