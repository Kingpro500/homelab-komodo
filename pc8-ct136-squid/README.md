# Squid (pc8 / CT136)

- Forward-proxy 10.0.0.212:3128, kun fra 10.0.0.0/8, ingen SSL-bump (HTTPS går som CONNECT-tunnel).
- Cache 20 GB på Unraid `proxmox-iso/squid` → `/data/squid` i CT136.
- Klienter må sette proxy selv; ingenting rutes automatisk.
