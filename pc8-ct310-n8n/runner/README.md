# CT reconcile runner

This is the durable orchestration boundary for the generic VMID workflow. It owns SQLite jobs/events and VMID leases. Privileged integrations (Proxmox, Komodo, GitHub, Periphery, Docker, and network-map updates) must be added as authenticated adapters; the runner must not claim `DONE` until each verification returns an explicit success.

## Local smoke test

```sh
CT_RECONCILE_PORT=9120 CT_RECONCILE_DB=/tmp/ct-reconcile.db python3 runner/ct_reconcile_runner.py
curl -sS http://127.0.0.1:9120/health
curl -sS -X POST http://127.0.0.1:9120/ct-reconcile -H 'content-type: application/json' -d '{"vmid":220}'
```

Set `CT_RECONCILE_TOKEN` in the service environment for authenticated requests. Never place its value in Git or n8n exports.
