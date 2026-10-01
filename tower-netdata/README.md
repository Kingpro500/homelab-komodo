# Netdata — Tower

- **Komodo server / stack:** `tower-docker-host` / `tower-netdata`
- **Cloud:** connected to the shared Netdata Cloud room through secret Komodo
  variable `NETDATA_CLAIM_TOKEN`.

The host network, PID namespace and read-only host mounts are intentional: this
agent observes Tower and its Docker engine. It does not publish a separate port;
use Netdata Cloud for the dashboard.
