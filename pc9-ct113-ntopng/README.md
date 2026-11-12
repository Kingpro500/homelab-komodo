# Network monitoring — CT113 (pc6)

- **CT:** 113 (`pc6-ct113-smokeping-ntopng`) on **pc6**. The directory name `pc9-ct113-ntopng` is historical and is kept because the Komodo stack path points to it.
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

## Deferred: full-LAN traffic mirroring

**Note:** The plan below was written when CT113 ran on pc9. CT113 now runs on pc6, so the NIC, bridge and cabling steps must be redone for pc6 before implementation.

**Status:** Postponed until approximately 8 November 2026. Ntopng remains
operational on `eth0` with limited visibility in the meantime.

Planned implementation:

1. Connect pc9's currently unused physical interface `nic0` to a dedicated
   mirror-destination port on the EdgeSwitch 8 150W.
2. Configure the switch to mirror the relevant LAN/uplink source port(s) to
   that destination port. Do not reuse pc9's management port on `nic1`.
3. Create `vmbr1` on pc9 with `nic0` as bridge port and no host IP address.
4. Add a second CT113 interface (`eth1`) on `vmbr1` without an IP address.
5. Change Ntopng capture from `eth0` to `eth1`, redeploy, and verify that it
   observes traffic for hosts other than CT113 without disrupting management.

Before implementation, record the chosen EdgeSwitch source and destination
port numbers and confirm that a physical cable is connected to `nic0`.
