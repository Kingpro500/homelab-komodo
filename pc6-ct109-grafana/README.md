# Grafana — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-grafana`
- **Address:** `http://10.0.0.128:3000`
- **Runtime data:** `/opt/grafana/data` in CT109, kept outside Git.

The initial runtime data is a copy of Tower's former Grafana SQLite database.
Tower's original `/mnt/user/appdata/grafana` is retained as a rollback copy and
must not be mounted by this stack. Create the runtime directory once before the
first deploy, then give it to Grafana's container user:

```bash
install -d -m 750 /opt/grafana/data
chown -R 472:472 /opt/grafana/data
```

Komodo variable required: `GRAFANA_DATA_PATH=/opt/grafana/data`.

## Dashboards (version-controlled in `provisioning/dashboards/`)

File-based dashboard provisioning WORKS on this Grafana (13.2.3) — contrary to the
older note that it was skipped. Verified 6 Oct 2026: `homelab-overview` and
`unraid-storage` are both imported into the unified object store on start.

| Dashboard | uid | Data source | Purpose |
|---|---|---|---|
| Homelab – Ressurser | `homelab-overview` | Prometheus 30s | Per-gjest CPU/RAM/disk fra Proxmox |
| Unraid – Lagring (Tower) | `unraid-storage` | Prometheus 60s (job `unraid-storage`) | Array/disks/caches/shares fylling fra Unraid GraphQL |

Recreate the container after adding a dashboard JSON — `docker kill --signal=HUP`
does NOT pick up new files (bind mount holds the old inode until recreate):
`docker-compose up -d --force-recreate grafana`.

