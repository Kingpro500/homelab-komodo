# Vikunja + Leantime — CT400

- Proxmox: CT400 on pc6 (10.0.0.120)
- IP: 10.0.0.33 (DHCP; reserve this address in DHCP before relying on it)
- Resources: 2 vCPU, 4 GiB RAM, 32 GiB local-lvm
- Privileged Docker CT, nesting enabled, autostart disabled
- Compose path: `/opt/vikunja-leantime/compose.yml`
- Vikunja: http://10.0.0.33:3456/
- Leantime: http://10.0.0.33:8080/

Secrets are generated only on the CT and are not stored in Git. The repository compose file requires the corresponding Komodo environment variables.

## Operations

```sh
pct start 400
pct exec 400 -- sh -c 'cd /opt/vikunja-leantime && docker compose ps'
pct exec 400 -- sh -c 'cd /opt/vikunja-leantime && docker compose logs --tail=100'
pct stop 400
```

## Komodo/GitOps

The compose definition is kept in `pc6-ct400-vikunja-leantime/`. Register a Komodo stack against the pc6 CT400 periphery, with the stack environment variables set in Komodo (never in Git). The live CT was initially bootstrapped directly because CT400 was new and had no periphery yet.
