# NetBox Stack

## Service
IPAM/DCIM platform for infrastructure management, device tracking, and network documentation.

## Components
- **NetBox app** (port 8001): Django web UI + API
- **PostgreSQL**: device inventory database
- **Redis**: cache and task queue
- **NetBox worker**: consumes queued and scheduled background jobs

## First-time setup

1. **Komodo stack configuration:**
   - Stack name: `pc8-ct102-netbox`
   - Server: `pc8-ct102-core`
   - Run directory: `stacks/pc8-ct102-netbox`
   - File paths: `docker-compose.yml`
   - Source: `https://github.com/Kingpro500/homelab-komodo`, branch `main`
   - Stack Environment: configure `POSTGRES_PASSWORD`, `SECRET_KEY`,
     `SUPERUSER_PASSWORD`, and `SUPERUSER_EMAIL` in Komodo. Do not commit
     or maintain a runtime `.env` file for this stack.

2. **After Komodo creates the stack, deploy it:**
   - Komodo UI → Stacks → `pc8-ct102-netbox` → Deploy
   - Wait for containers to start (~30s)

3. **Access NetBox:**
   - URL: `http://10.0.0.117:8001`
   - Sign in using the superuser configured in Komodo.

4. **Generate API token:**
   - NetBox UI → Admin → Users → admin → API Tokens → Generate
   - Copy token, paste into Scanopy `.env` as `NETBOX_TOKEN`

## Volumes
- `postgres_data`: persistent device database
- `netbox_config`: configuration directory
- `netbox_media`: uploaded files and exports
- `redis_data`: cache snapshots

## Ports
- 8001: NetBox web interface

## Documentation
- NetBox: https://docs.netbox.dev
- API: http://10.0.0.117:8001/api/docs/
