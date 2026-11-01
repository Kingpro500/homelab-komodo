# Network monitoring — pc9 CT113

- **CT:** 113 on pc9
- **Ntopng:** `http://10.0.0.171:3000`
- **SmokePing:** `http://10.0.0.171:3001/smokeping/`
- **Deployment:** Komodo GitOps from `Kingpro500/homelab-komodo`
- **Edition:** Community
- **Capture interface:** `eth0`
- **Persistent data:** `/opt/ntopng/data`

SmokePing stores configuration in `/opt/smokeping/config` and time-series data
in `/opt/smokeping/data`. Its targets are managed in
`/opt/smokeping/config/Targets` after the first start.

The container uses host networking with Docker's default capability set plus `NET_ADMIN` for packet capture.
Logs are bounded by Docker log rotation.

## Visibility limitation

An ordinary bridged LXC interface primarily sees traffic addressed to CT113,
plus broadcast and multicast traffic. Full-LAN analysis requires a mirrored
switch port, a dedicated capture interface, or NetFlow/sFlow/IPFIX export from
the router or switches to a collector.
