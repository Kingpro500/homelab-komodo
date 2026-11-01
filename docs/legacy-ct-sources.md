# Legacy CT source inventory

Verified against live Proxmox configuration, stopped container root filesystems,
Komodo Core, and the Git repository on 1 November 2026. These containers are
archives and should not be represented as active Komodo stacks.

| VMID | Hostname | Runtime | Source status | Komodo |
|---|---|---|---|---|
| PC6 CT108 | `ct108-legacy-dockere-gammel` | Stopped; autostart off | No Compose file found under `/opt`, `/root`, or `/srv`. GitHub contains documentation only in `pc6-ct108-legacy-dockere/README.md`. | No matching server or stack |
| PC6 CT235 | `ct159-audiobookshelf-ngrok-gammel` | Stopped; autostart off; stale mount lock cleared 2026-11-01 | GitHub contains the legacy Audiobookshelf source in `pc6-ct109-audiobookshelf/`. No current ngrok Compose source was found in GitHub. Rootfs was not inspected during this audit. | Only the detached legacy stack `pc6-ct109-audiobookshelf` exists |
| PC6 CT240 | `ct160-lancache-gammel` | Stopped; autostart off | Compose exists only inside the archived CT at `/opt/legacy-services/docker-compose.yml`; no matching GitHub source was found. | No matching server or stack |
| PC6 CT390 | `ct112-openwebui-gjeld-gammel` | Stopped; autostart off | Compose exists only inside the archived CT at `/opt/gjeld/docker-compose.yml`. Related app/setup files exist under `pc6-ct154-paperless/gjeld/`, but they are not a CT390 deployment source. | No matching server or stack |
| PC6 CT392 | `ct114-dashboards-gammel` | Stopped; autostart disabled 2026-11-01 | DiskSpeed Compose exists at `/opt/diskspeed/docker-compose.yml`. Other local Compose files exist below `/opt/dashboards/` and `/opt/open-webui-stack/`; GitHub only has older sources under other CT names. | No matching server or stack |

## Policy

- Do not create Komodo resources for these CTs while they remain stopped archives.
- Do not deploy older GitHub sources without first comparing volumes, environment
  variables, image versions, and application data.
- If a service is revived, sanitize its local Compose source into a new
  VMID-correct GitHub directory, create a fresh Komodo server/stack, and verify
  the application before retiring the legacy source.
