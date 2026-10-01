# iVentoy on pc6 CT 111

- **Host:** pc6 (`10.0.0.120`)
- **LXC:** `pc6-ct111-iventoy`
- **IP:** `10.0.0.134`
- **Web UI:** `http://10.0.0.134:26000`
- **ISO storage:** Tower `Unraid-ISO`, mounted at `/iso` in the LXC

iVentoy is isolated because PXE needs UDP 67 (DHCP proxy) and UDP 69 (TFTP),
and its Docker image requires privileged mode. The ISO directory remains on
Tower; only iVentoy configuration and logs live under `/opt/iventoy` inside the
LXC.

## Network notes

The PXE service is enabled automatically. Configure only one DHCP/PXE proxy on
the LAN, and do not enable iVentoy DHCP if OPNsense already provides DHCP. Add
a DHCP reservation for `10.0.0.134` in OPNsense before relying on the service.
