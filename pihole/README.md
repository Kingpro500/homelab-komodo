# Pi-hole through Komodo

Deploy this Compose file from GitHub using a Komodo Stack on a Docker host managed by Periphery.

## Setup

Link the GitHub Repo in the Stack, select the target Server, set Run Directory to `pihole` and Compose file to `docker-compose.yml`.

Create a unique random password in Komodo Settings → Variables with **Secret** enabled, then configure the Stack environment:

```dotenv
PIHOLE_BIND_IP=<target-host-LAN-IP>
PIHOLE_HOSTNAME=<instance-name>
PIHOLE_WEB_PASSWORD=[[YOUR_PIHOLE_SECRET_NAME]]
```

Use a separate IP, secret and persistent volume for each instance. Compose rejects missing/empty passwords and binding IPs. DNS uses TCP/UDP 53; the web interface uses port 8080 at `/admin/`. DHCP remains with the existing DHCP server. Test each DNS instance before updating client DNS settings. Docker Swarm is not required.

## Credential handling rule

Git stores configuration and secret references only. Store application passwords and API keys in Komodo secret variables, referenced with `[[NAME]]`. Never put actual values in Compose files, commits, issue descriptions or logs. Komodo writes a deployment `.env` on the target: restrict access to administrators/the deployment service and keep it outside Git.

The repository ignores local `.env` files, private key files and runtime data. Ignoring a file does not remove historical exposure: rotate any credential that has been committed. Keep a secure password-manager copy for disaster recovery. Restrict Komodo admin access and protect its database backups.

## Persistence and migration

Pi-hole settings and databases are stored in the project-scoped Docker volume `pihole_data`. Redeploying retains this volume. Changing the Stack target server alone does not transfer data.

When Docker runs inside a Proxmox LXC, migrating/restoring the entire LXC can preserve the disk, application data and network identity. Stop the source, migrate/restore its disk, verify network and storage on the target, then start and test. Never start two copies with the same IP. Alternatively, use Pi-hole Teleporter or a consistent volume backup to transfer application data.

Keep independent backups; snapshots alone are not backups. Reusable base templates must exclude passwords, API tokens, SSH host keys, Periphery private identities, fixed network addresses and Swarm membership. New clones need unique identities. A migration retains the existing instance identity.

Image versions are pinned in Compose and updated through GitHub. This stack does not configure automatic failover.
