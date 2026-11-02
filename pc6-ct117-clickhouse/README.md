# ClickHouse på pc6 / CT117

GitOps-kilde for en enkel ClickHouse LTS-node administrert av Komodo.

## Mål

- Komodo-server: `ct117`
- Adresse: `10.0.0.175`
- HTTP: `http://10.0.0.175:8123`
- Native TCP: `10.0.0.175:9000`
- Minimum før deploy: 4 vCPU, 4 GB RAM, 32 GB disk
- Anbefalt: 4 vCPU, 6-8 GB RAM og egen datadisk

CT117 har ved opprettelsen bare 1 vCPU, 512 MB RAM og 8 GB disk. Stacken må
ikke deployes før kapasiteten er økt.

## Komodo secrets

- `CLICKHOUSE_PASSWORD`

Valgfrie, ikke-hemmelige variabler:

- `CLICKHOUSE_DB` (standard `homelab`)
- `CLICKHOUSE_USER` (standard `homelab`)

## Komodo-stack

- Navn: `pc6-ct117-clickhouse`
- Repo: `https://github.com/Kingpro500/homelab-komodo`
- Branch: branch som inneholder denne mappen, deretter `main` etter merge
- Run directory: `pc6-ct117-clickhouse`
- Compose: `docker-compose.yml`

Begrens port 8123 og 9000 i Proxmox-brannmuren til CT109 og andre eksplisitte
datakilder. Volumene skal inngå i ordinær backup.
