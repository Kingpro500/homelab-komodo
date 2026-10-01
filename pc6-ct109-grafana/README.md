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
