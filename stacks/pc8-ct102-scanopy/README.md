# Scanopy Stack

## Service
Network discovery and topology mapping via SNMP, integrated with NetBox for device correlation.

## Components
- **Scanopy**: SNMP network scanner and topology visualizer
- Uses NetBox API for device correlation
- Requires SNMP community access to network devices

## First-time setup

1. **Ensure NetBox is running and has an API token**
   - See `../pc8-ct102-netbox/README.md` for NetBox setup

2. **Create the stack in Komodo UI:**
   - Stack name: `pc8-ct102-scanopy`
   - Server: `pc8-ct102-komodo`
   - Run directory: `/opt/stacks/pc8-ct102-scanopy`
   - File paths: `docker-compose.yml`
   - **Important:** This stack reuses the `netbox` network from the NetBox stack

3. **Configure Scanopy:**
   - Edit `.env` in the Komodo run directory:
     - `NETBOX_TOKEN`: paste the token from NetBox admin panel
     - `SNMP_COMMUNITY`: your network's SNMP community string (default: `public`)
   - Add subnet ranges or device IPs for discovery

4. **Deploy and start discovery:**
   - Komodo UI → Deploy
   - Access: `http://10.0.0.117:8002`

## Network sharing
Both stacks use the same Docker network (`netbox`) so containers can communicate.
Scanopy reaches NetBox internally via `http://netbox:8080`.

## Ports
- 8002: Scanopy web interface

## Limitations
- Requires devices to respond to SNMP v2c (or configured version)
- Discovery is best-effort; unreachable devices are skipped
- Token must have read access to NetBox devices and interfaces

## Documentation
- Scanopy: https://github.com/nicolaka/scanopy
- NetBox API: http://10.0.0.117:8001/api/docs/
