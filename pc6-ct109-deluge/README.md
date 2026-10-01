# Deluge with VPN — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-deluge`
- **Web UI:** `http://10.0.0.128:8112`
- **Downloads:** Tower media storage is mounted read/write at `/data`; no downloads
  or media are copied.
- **Network:** Deluge has no direct network. All traffic passes through the
  Gluetun OpenVPN container with its firewall enabled (kill-switch).

Required Komodo variables:

```text
DELUGE_CONFIG_PATH=/opt/deluge/config
DELUGE_VPN_CONFIG_PATH=/opt/deluge/vpn
```

`/opt/deluge/vpn` is copied directly from Tower and contains VPN credentials.
It must never be committed to Git or pasted into Komodo variables. The source
Tower container remains stopped as rollback until the migrated service has been
verified.
