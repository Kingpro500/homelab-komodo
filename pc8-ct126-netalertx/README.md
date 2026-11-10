# pc8-ct126-netalertx

- **Host:** pc8 CT126 (`netalertx`, `10.0.0.177`), Debian 13, 1 vCPU / 1 GB RAM / 8 GB disk
- **Komodo server:** `pc8-ct126-netalertx` (systemd Periphery v2.3.3, registered with `scripts/ct-komodo.sh`)
- **Web UI:** `http://10.0.0.177:20211/` (GraphQL backend on 20212)
- **Purpose:** detect new/unknown devices on 10.0.0.0/24 and alert.
- **Data:** Docker volume `netalertx_data` (`/data`: config + database).
- **Image:** pinned `ghcr.io/netalertx/netalertx:26.10.28`; upgrade by changing the tag here.

Notes: runs with `network_mode: host` for ARP scanning. The upstream `sysctls`
block is removed because Docker refuses sysctls in the host network namespace
inside an LXC.
