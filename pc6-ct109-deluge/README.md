# Deluge — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-deluge`
- **Web UI:** `http://10.0.0.128:8112`
- **Downloads:** Tower media storage is mounted read/write at `/data`; no downloads
  or media are copied.
- **Network:** direct LAN operation. It is intentionally not routed through a
  VPN at present.

Required Komodo variables:

```text
DELUGE_CONFIG_PATH=/opt/deluge/config
```

The source Tower container remains stopped as rollback until the migrated
service has been verified. A previous VPN configuration is retained locally on
CT109 only; it is not committed to Git or used by this stack.
