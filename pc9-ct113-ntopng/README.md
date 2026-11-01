# Ntopng — pc9 CT113

- **CT:** 113 on pc9
- **Address:** `http://10.0.0.171:3000`
- **Deployment:** Komodo GitOps from `Kingpro500/homelab-komodo`
- **Edition:** Community
- **Capture interface:** `eth0`
- **Persistent data:** `/opt/ntopng/data`

The container uses host networking with only `NET_ADMIN` and `NET_RAW` added.
Logs are bounded by Docker log rotation.

## Visibility limitation

An ordinary bridged LXC interface primarily sees traffic addressed to CT113,
plus broadcast and multicast traffic. Full-LAN analysis requires a mirrored
switch port, a dedicated capture interface, or NetFlow/sFlow/IPFIX export from
the router or switches to a collector.
