# Lancache og Squid (pc8 / CT136)

| Tjeneste | Adresse | Stack | Data (Unraid `proxmox-iso`) |
| --- | --- | --- | --- |
| Lancache | 10.0.0.212:80/443 | `pc8-ct136-lancache` | `lancache/cache` (100 GB), `lancache/logs` |
| Squid | 10.0.0.212:3128 | `pc8-ct136-squid` | `squid` (20 GB) |

- CT136 på pc8: 2 kjerner, 4 GB RAM. Unraid-mappene er montert som `mp0`/`mp1` (`/data/lancache`, `/data/squid`).
- Plassert på pc8 fordi pc7 har lite ledig RAM. Cachen ligger på Unraid, så Emby-lagringen berøres ikke.
- Pi-hole-integrasjon: legg cache-domenene (uklans/cache-domains) som `address=/<domene>/10.0.0.212` i `misc.dnsmasq_lines`. Pi-hole beholdes, `lancache-dns` brukes ikke.
- Rollback: fjern dnsmasq-linjene, klientene går direkte ut igjen.
- Homepage-flis og nettverkskart-oppføring (Gitea) gjenstår og føres inn i samme runde som deploy.
