# iVentoy on pc6 CT 111

- **Host:** pc6 (`10.0.0.120`)
- **LXC:** `pc6-ct111-iventoy`
- **IP:** `10.0.0.134`
- **Web UI:** `http://10.0.0.134:26000`
- **ISO storage:** Tower `Unraid-ISO`, mounted at `/iso` in the LXC

iVentoy is isolated because PXE needs UDP 67 (DHCP proxy) and UDP 69 (TFTP),
and its Docker image requires privileged mode and host networking. Host
networking is necessary for LAN broadcast PXE traffic; CT 111 is dedicated to
iVentoy so no other application can conflict with its ports. The ISO directory
remains on Tower; only iVentoy configuration and logs live under
`/opt/iventoy` inside the LXC.

## Network notes

The PXE service is enabled automatically. Configure only one DHCP/PXE proxy on
the LAN, and do not enable iVentoy DHCP if OPNsense already provides DHCP.

CT 111 uses the static address `10.0.0.134`, outside the active Kea dynamic
pool (`10.0.0.2`–`10.0.0.99`). Do not add a Kea reservation for it: the static
address already avoids the pool and this avoids the known outside-pool
reservation edge case.
