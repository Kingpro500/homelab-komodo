# Pi-hole through Komodo

Deploy this Compose file from GitHub using a Komodo Stack on a Docker host managed by Periphery.

## Setup

Link the GitHub Repo in the Stack, select the target Server, set Run Directory to `pihole` and Compose file to `docker-compose.yml`.

Create a unique random password in Komodo Settings → Variables with **Secret** enabled, then configure the Stack environment:

```dotenv
PIHOLE_BIND_IP=<target-host-LAN-IP>
PIHOLE_HOSTNAME=<instance-name>
PIHOLE_UPSTREAM_DNS=<upstream-resolver-IP>#53
# Optional local forward/reverse DNS:
PIHOLE_REVERSE_SERVERS=true,<LAN-CIDR>,<local-resolver-IP>#53,<local-domain>
PIHOLE_WEB_PASSWORD=[[YOUR_PIHOLE_SECRET_NAME]]
```

Use a separate IP, secret and persistent volume for each instance. Compose rejects missing/empty passwords, binding IPs and upstream DNS settings. DNS uses TCP/UDP 53; the web interface uses port 8080 at `/admin/`. DHCP remains with the existing DHCP server. Test each DNS instance before updating client DNS settings. Docker Swarm is not required.

Use an upstream resolver reachable from the Docker host (for example, your router’s Unbound service). Multiple upstreams are separated by semicolons. Local domains such as `internal` require explicit conditional forwarding via `PIHOLE_REVERSE_SERVERS`; configure it when the upstream resolver owns your local records. Leave it empty if unused. Avoid DNS loops: the upstream resolver must not forward requests back to these Pi-hole instances.

## DNS chain in this homelab

```text
client ──(Kea DHCP gives 10.0.0.115 / 10.0.0.116)──▶ Pi-hole
                                                             │
                                          PIHOLE_UPSTREAM_DNS=10.0.0.1#53
                                                             ▼
                                       Unbound on OPNsense (10.0.0.1)
                                             │                    │
                        lan.local host overrides            1.1.1.1 (system DNS)
                        (homeassistant, bridge, ac-pro,        via General → Settings
                         espcontrol-*, media-player,           → DNS Servers
                         pihole-pc8/9, komodo, pve, pc9)
                                             │                    │
                                             └───── internet ───┘
```

Two instances, one Compose file:

| Stack | Container host | IP | Upstream |
|---|---|---|---|
| `pc8-ct115-pihole` | `pihole-pc8` | 10.0.0.115 | 10.0.0.1#53 |
| `pc9-ct116-pihole` | `pihole-pc9` | 10.0.0.116 | 10.0.0.1#53 |

See `.env.example` for the exact Stack Environment values. Passwords are secret
references only, never values.

### Why the local domain must match Unbound

`PIHOLE_REVERSE_SERVERS` ends with the local domain. It must be the same string as
the Domain column of the Unbound Host Overrides in OPNsense
(Services → Unbound DNS → Overrides), which is `lan.local`. Clients also receive
`search lan.local` from Kea, so an unqualified name such as `homeassistant` is
resolved as `homeassistant.lan.local`.

If the two disagree, local names fail silently: Unbound has no matching record and
Pi-hole returns nothing, with no error on either side. This is the single most
fragile value in this stack.

### DNS loop

Pi-hole forwards `lan.local` to Unbound; Unbound resolves it locally and never
forwards to Pi-hole. Upstream must stay a resolver that does not point back here.
Changing `PIHOLE_UPSTREAM_DNS` to either Pi-hole address creates a loop.

### Client hand-over

Clients are moved onto Pi-hole by pointing the Kea DHCP server at `10.0.0.115` and
`10.0.0.116`. Until that is done, clients query `10.0.0.1` directly, Unbound answers
everything, and Pi-hole filtering is bypassed entirely. Keep `94.140.14.14` as a third
server so DNS survives both instances being down. Lease renewal is what hands the new
servers to clients; existing clients keep the old ones until renewal.

Verify with:

```bash
dig @10.0.0.115 github.com
dig @10.0.0.115 homeassistant.lan.local   # expect 10.0.0.7
dig @10.0.0.1   github.com
```

## Credential handling rule

Git stores configuration and secret references only. Store application passwords and API keys in Komodo secret variables, referenced with `[[NAME]]`. Never put actual values in Compose files, commits, issue descriptions or logs. Komodo writes a deployment `.env` on the target: restrict access to administrators/the deployment service and keep it outside Git.

The repository ignores local `.env` files, private key files and runtime data. Ignoring a file does not remove historical exposure: rotate any credential that has been committed. Keep a secure password-manager copy for disaster recovery. Restrict Komodo admin access and protect its database backups.

## Persistence and migration

Pi-hole settings and databases are stored in the project-scoped Docker volume `pihole_data`. Redeploying retains this volume. Changing the Stack target server alone does not transfer data.

When Docker runs inside a Proxmox LXC, migrating/restoring the entire LXC can preserve the disk, application data and network identity. Stop the source, migrate/restore its disk, verify network and storage on the target, then start and test. Never start two copies with the same IP. Alternatively, use Pi-hole Teleporter or a consistent volume backup to transfer application data.

Keep independent backups; snapshots alone are not backups. Reusable base templates must exclude passwords, API tokens, SSH host keys, Periphery private identities, fixed network addresses and Swarm membership. New clones need unique identities. A migration retains the existing instance identity.

Image versions are pinned in Compose and updated through GitHub. This stack does not configure automatic failover.
