# Ansible Semaphore på pc6 / CT109

GitOps-kilde for Semaphore UI med PostgreSQL. Semaphore-containeren leverer
Ansible-kontrollplanet; det skal ikke kjøres en separat, permanent
Ansible-container.

## Mål

- Komodo-server: `ct109`
- Adresse: `10.0.0.174`
- Web: `http://10.0.0.174:3000`
- Anbefalt kapasitet før deploy: 4 vCPU, 4 GB RAM, 24 GB disk

## Komodo secrets

Opprett disse som Secret Variables i stack-miljøet:

- `SEMAPHORE_DB_PASSWORD`
- `SEMAPHORE_ADMIN_PASSWORD`
- `SEMAPHORE_ACCESS_KEY_ENCRYPTION` (32 tilfeldige bytes, base64-kodet)

Ingen av verdiene skal lagres i Git. SSH-nøkler og Ansible Vault-passord legges
i Semaphore Key Store etter første innlogging.

## Komodo-stack

- Navn: `pc6-ct109-ansible-semaphore`
- Repo: `https://github.com/Kingpro500/homelab-komodo`
- Branch: branch som inneholder denne mappen, deretter `main` etter merge
- Run directory: `pc6-ct109-ansible-semaphore`
- Compose: `docker-compose.yml`

Installer collection-avhengigheter i Semaphore-prosjektets første task med:

```sh
ansible-galaxy collection install -r requirements.yml
```

PostgreSQL-porten publiseres ikke på verten. Bare Semaphore UI eksponeres.
