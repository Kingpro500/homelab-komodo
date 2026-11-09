# Homelab inventory

This file is no longer a hand-maintained guest list. A manual copy drifted
out of date (wrong CT numbers, IP addresses and DNS servers), so it has been
replaced by pointers to the systems that hold the live truth.

| Question | Source of truth |
| --- | --- |
| Which CTs/VMs exist, their node, status, CPU, memory and disk | Proxmox (CyberCluster), live |
| Assets, IP addresses, interfaces, cables and dependencies | NetBox `http://netbox.lan.local:8001/` (synced from Proxmox nightly by `netbox-proxmox-sync.timer` on PC6, 04:30) |
| How each service is deployed (compose and config) | This repository, one directory per Komodo stack |
| Which Komodo server/stack runs where | Komodo Core `http://10.0.0.117:9120/` |
| Access routes and agent rules | `docs/network-map/ACCESS-RUNBOOK.md` |
| Network map and monitoring page | Gitea (published by `nettkart-publish` on PC6/CT120) |

## DNS (verified 2026-11-08)

- Kea DHCP on OPNsense hands out `10.0.0.115` (PC6 CT101 Pi-hole) and
  `10.0.0.118` (PC9 CT103 Pi-hole reserve). Both are always on.
- `10.0.0.116` (PC1 CT102 Pi-hole) only runs when PC1 is booted into Proxmox
  and is not handed out by DHCP.
- Pi-hole upstream is Unbound on OPNsense (`10.0.0.1`). Proxmox nodes resolve
  directly via `10.0.0.1` so they do not depend on a Pi-hole CT.
- No NAT rule forces client DNS to Pi-hole.

## Address notes (verified 2026-11-08)

- PC9 CT203 Emby standby moved from `10.0.0.127` to `10.0.0.203` because
  PC6 CT230 (Immich) also uses `10.0.0.127`.
