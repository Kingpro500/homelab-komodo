# Lancache (pc8 / CT136)

- Vert: `pc8-ct136-ct136`, 10.0.0.212, porter 80/443.
- Image: `lancachenet/monolithic`. Cache: 100 GB (`CACHE_DISK_SIZE`), indeks 125 MB.
- Data: Unraid `proxmox-iso/lancache/{cache,logs}` → montert i CT136 som `/data/lancache`.
- DNS: Pi-hole sender cache-domenene til 10.0.0.212 (`misc.dnsmasq_lines`, se `docs/operations/lancache-squid.md`).
- Kun HTTP-cache. DoH/DoT hos klienter omgår cachen. Ved problemer: fjern dnsmasq-linjene i Pi-hole, så går trafikken rett ut igjen.
