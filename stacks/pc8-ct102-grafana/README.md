# Grafana Stack

## Service
Metrics visualization, dashboards, and alerting platform. Visualizes NetBox inventory, system metrics, and network topology.

## Components
- **Grafana**: dashboard and visualization engine
- **PostgreSQL**: dashboard and user database

## First-time setup

1. **Create the stack in Komodo UI:**
   - Stack name: `pc8-ct102-grafana`
   - Server: `pc8-ct102-komodo`
   - Run directory: `/opt/stacks/pc8-ct102-grafana`
   - File paths: `docker-compose.yml`

2. **After Komodo creates and deploys the stack:**
   - Access: `http://10.0.0.117:3000`
   - Default credentials: `admin` / `admin` (change immediately)

3. **Add NetBox as a data source:**
   - Grafana → Administration → Data sources → Add
   - Type: **JSON API**
   - Name: `NetBox`
   - URL: `http://netbox:8080/api` (internal Docker DNS)
   - Auth header: `Authorization: Token your_api_token_here`
   - Click **Save & Test**

4. **Optional: Add Prometheus (if metrics collection is set up)**
   - Data source type: **Prometheus**
   - URL: `http://prometheus:9090`

## Dashboards to create
- Infrastructure overview (NetBox device count, site status)
- Network topology (from Scanopy SNMP data)
- Storage capacity trends
- System uptime and alerts

## Volumes
- `grafana_storage`: dashboard definitions, user settings
- `postgres_data`: persistent dashboard database

## Ports
- 3000: Grafana web interface

## Integration with other stacks
- **NetBox**: read device and interface data via JSON API datasource
- **Scanopy**: can import topology as JSON datasource
- **Home Assistant**: expose metrics via a JSON HTTP endpoint or use official HA Grafana integration

## Documentation
- Grafana: https://grafana.com/docs/
- JSON API: https://grafana.com/docs/grafana/latest/datasources/json-api/
- NetBox API: http://10.0.0.117:8001/api/docs/
