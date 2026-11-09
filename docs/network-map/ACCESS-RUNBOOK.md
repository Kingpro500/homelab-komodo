# Homelab access runbook

This is the operational source of truth for Codex access checks. It documents
access paths and verification steps, never secret values. Update it whenever
an integration, host, or credential location changes.

## Repository boundary — read first

| Repository | Used for | Nothing else |
| --- | --- | --- |
| **GitHub** `git@github.com:Kingpro500/homelab-komodo.git` | Everything: stacks, automation, scripts, operational documentation and **this runbook** | — |
| **Gitea** `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git` | **Only** the network map (`docs/network-map/nettverkskart.html` and its versions) and the monitoring page (`docs/network-map/daily-report.html`), published through `nettkart-publish` on PC6/CT120 | Do not commit or push anything else there, not even on a branch |

This runbook is maintained **only in GitHub**. The Gitea repository still
contains older copies of other files, including a short `ACCESS-RUNBOOK.md`.
Those copies are not authoritative and must not be edited or used as a source.


## Mandatory agent behaviour

1. Read this runbook before saying access is missing or a homelab system is
   unavailable.
2. Use the documented path and perform a safe read-only check first.
3. A missing direct connector does **not** mean the system is inaccessible;
   use the documented SSH, API, or service route.
4. Report an exact failed route only after trying it. Do not ask the user to
   repeat known access details or debate whether an integration exists.
5. Read-only verification is normal diagnostics. Any change, restart, deploy,
   credential rotation, or configuration write still requires a task request.

## Credential references and scope

Only these local Codex secret references are currently used for homelab
automation. They are unversioned regular files in `~/.codex/secure/`, mode
`0600`, and their values must never be displayed, copied, committed, or put in
NetBox/the network map:

| Reference | Used for | Current audit |
| --- | --- | --- |
| `homelab-netbox.env` | NetBox URL and v2 bearer token | working, 6 November 2026 |
| `homelab-unifi.env` | UniFi Network controller session login | working, 6 November 2026 |
| `homelab-edgeswitch.env` | EdgeSwitch WebUI/SSH login | WebUI and SSH CLI working; internal WebUI API login returns HTTP 403, 6 November 2026 |

Configuration backups stored beside these files are protected operational
artifacts, not credential sources. Do not inspect or publish them.

## OPNsense — pc7, `10.0.0.1`

**Known working path:** Hermes, CT130 on PC6 (`10.0.0.120`). The API
credentials are held only in `/home/hermes/.hermes/.env` inside CT130. They
must never be displayed, copied, or committed.

The currently deployed Hermes services use authenticated HTTPS calls to these
read endpoints:

- `/api/diagnostics/interface/getInterfaceStatistics`
- `/api/routes/gateway/status`
- `/api/diagnostics/interface/getArp`
- `/api/diagnostics/log/core/system`

The collector and five-second sampler are active on CT130. Hermes stores its
observations locally in SQLite and exposes safe Prometheus metrics on port
`9130`.

**Required response to an OPNsense request:** do not claim that Codex lacks
OPNsense access merely because there is no direct OPNsense MCP connector or
browser login. Start through Hermes. The API has been live-verified on
4 November 2026. Its credentials also successfully read firewall-rule data;
therefore treat the account as sensitive and do not probe write endpoints
without an explicit change request.

**Known accounts:** `codex-opnsense` is an administrative OPNsense account in
the 5 October 2026 configuration backup. Its credential is not stored in this
repository. `hermes` is the deployed monitoring/API account. Never substitute
or rotate either account without instruction.

## Proxmox — CyberCluster

**Known working path:** the Proxmox MCP integration provides cluster status,
resource list, node overview, guest configuration and recent tasks. It is
read-only. It was live-verified on 4 November 2026.

For host- or container-level diagnostics not exposed by MCP, the documented
route is the managed SSH deployment identity to a Proxmox node, followed by
read-only `pct` diagnostics. Do not mistake the lack of console permissions
for a lack of Proxmox visibility.

**Managed SSH route:** the Codex deployment identity at
`~/.ssh/codex_fleet_deploy` is the administrative transport to Proxmox nodes.
Use `BatchMode=yes`, `IdentitiesOnly=yes`, and an explicit target node, then
use `pct` for a narrowly scoped guest check. It is not a general-purpose
credential store and the private-key material must never be copied or printed.
PC6 (`10.0.0.120`) and its running CT101, CT113, CT120, and CT130 were
live-verified through this route on 6 November 2026.

## SSH access matrix

There are two deliberately different SSH paths. Do not treat a failed
restricted guest login as a failure of the PC6 administrative transport, or
vice versa.

| Target | Address / route | Access level | Verification state |
| --- | --- | --- | --- |
| PC6 Proxmox | `10.0.0.120`, direct managed deployment identity | Administrative transport for explicitly requested node/guest operations; use narrow `pct` diagnostics by default | Live-verified 6 November 2026 |
| CT101 Pi-hole | via PC6 `pct exec 101` | Guest diagnostics through PC6; no claim of a separate direct SSH route | Live-verified 6 November 2026 |
| CT113 Smokeping/ntopng | via PC6 `pct exec 113` | Guest diagnostics through PC6 | Live-verified 6 November 2026 |
| CT120 NetBox/network map | via PC6 `pct exec 120` | Guest diagnostics and the documented NetBox maintenance route | Live-verified 6 November 2026 |
| CT130 Hermes | via PC6 `pct exec 130` | Guest diagnostics; preferred path for OPNsense and UniFi monitoring | Live-verified 6 November 2026 |
| PC9 / CT106 / CT108 | direct `codex-fleet-readonly` path where installed | Forced-command, read-only diagnostics only; no shell, Docker socket, file reads, restarts, or package management | Historically verified; re-check before claiming a current direct session |
| PVE / CT115 | direct `codex-fleet-readonly` path where installed | Forced-command, read-only diagnostics only | Historically verified; re-check before claiming a current direct session |
| PC1 | Proxmox visibility through MCP when online | No current SSH claim; node was previously unavailable | Do not infer direct SSH access |
| OPNsense | no SSH route documented for Codex | Use Hermes authenticated API path | API route live-verified 4 November 2026 |
| Tower/Unraid and Windows | no active Codex SSH route documented | Planned only | Do not claim access |

The restricted `codex-fleet-readonly` identity never grants an interactive
shell or state-changing privilege. The managed PC6 deployment identity is a
separate, sensitive administrative route: use it only for the requested task
and prefer read-only checks. Neither private key nor a command line containing
credential material may be printed, copied, committed, or added to NetBox.

## NetBox — CT120 on PC6

**Known working path:** NetBox runs on CT120 (`10.0.0.124`) and is available
at `http://netbox.lan.local:8001/`. It was live-verified on 4 November 2026:
the CT and `netbox-app`, `netbox-worker`, PostgreSQL, and Redis containers
were running, and the correctly addressed HTTP request redirected to login.

**Automation credential:** the local, unversioned file
`~/.codex/secure/homelab-netbox.env` (mode `0600`) contains `NETBOX_URL` and
`NETBOX_API_TOKEN`. The latter is a complete NetBox v2 bearer token for the
`admin` user and has write permission for the requested inventory automation.
Never print, copy, commit, or add either value to NetBox/map documentation.

Safe verification:

```sh
set -a; source ~/.codex/secure/homelab-netbox.env; set +a
curl -fsS -H "Authorization: Bearer $NETBOX_API_TOKEN" \
  "$NETBOX_URL/api/status/"
```

Use NetBox for topology and inventory; do not claim it is unavailable merely
because an API token is not present in the local workspace.

**Container maintenance route:** when an explicitly requested topology change
cannot use the bearer-token route, managed SSH to PC6 followed by CT120's
`netbox-app` Django management context is available. Its superuser configuration
remains inside CT120 and must never be printed or exported. Read current objects
first and make idempotent, narrowly scoped changes. This route created and
verified the UniFi passive mirror topology on 5 November 2026.

## UniFi Network — `10.0.0.132:8443`

**Known path:** the UniFi Network controller is administered at
`https://10.0.0.132:8443/`. Its local Codex-host credential reference is
`/Users/rogerlillefosse/.codex/secure/homelab-unifi.env`; the file is local,
not versioned, and must remain mode `0600`. An administrator user, `admin`,
is configured for Codex use. Never copy the password or other file contents
into this runbook, Git, NetBox, a network map, or chat.

For diagnostics, verify controller reachability and authenticate only when the
task requires UniFi data or changes. Do not mistake an unavailable direct path
from the Codex sandbox for a controller outage: retry through the documented
PC6 route when appropriate. The credential and PC6 route were live-verified
on 4 November 2026 (`HTTP 200`). UniFi configuration changes require an
explicit task request.

**Read-only monitoring path:** Hermes CT130 stores a protected deployment copy
at `/home/hermes/.hermes/unifi.env` (mode `0600`) and runs
`unifi-network-collector` every minute. It reads device, uplink and switch-port
status only, retains health history in its local monitoring SQLite database and
exports safe Prometheus metrics on port `9130`. The deployment was verified on
5 November 2026 through PC9 Prometheus. This path has no UniFi write calls.
PC9 alerts when collection has been unavailable for five minutes or switch
mirror port 4 has no link for two minutes; alerts are diagnostic only.
The same exporter now includes USW port 1/4 error and drop counters; PC9
alerts only on a sustained increase. PC9 independently probes controller HTTPS
on `10.0.0.132:8443` (availability only; the local controller certificate is
not used as a trust anchor for this diagnostic probe).

## EdgeSwitch 8 — `10.0.0.32`

**Known path:** management is HTTPS at `https://10.0.0.32/`.  The local,
unversioned credential reference is
`~/.codex/secure/homelab-edgeswitch.env` (mode `0600`); it contains only the
URL and login values and must never be displayed, copied into this runbook, or
committed.  Use the management UI or its authenticated API for an explicitly
requested configuration change.  First verify reachability with a safe HTTPS
GET.  NetBox is the inventory record for its management address and topology,
not a credential store.

**Current API status:** the expected new-WebUI route is
`POST /api/v1.0/user/login`, followed by `X-Auth-Token` on read-only
`GET /api/v1.0/device`, `/interfaces`, `/statistics`, and `/system`. On the
6 November 2026 audit, that login returned HTTP 403 and no token. Do not claim
API access is working and do not retry configuration writes through it until
the authentication method or account has been repaired. The HTTPS login page
itself is reachable. A protected pre-upgrade backup exists locally; never
print or inspect its contents in chat.

**Preferred automation route:** direct SSH CLI on TCP/22, using the same local
`homelab-edgeswitch.env` reference. It was authenticated and read-verified on
6 November 2026 with `show version`: ES-8-150W, firmware 1.12.2. Start every
task with display-only CLI commands such as `show version`, `show interfaces`
or `show running-config`; any configuration command requires an explicit task
request and a fresh backup. Do not use the unsupported internal WebUI API for
automation. The switch warns that CLI changes can affect device access, so keep
WebUI and CLI changes deliberate and documented.

**Passive capture quality:** CT113 exposes read-only eth1 kernel counters on
port `9102`; PC9 scrapes them as `passive-capture-interface`. Alerts cover
missing metrics, carrier loss and sustained RX drops. These counters measure
evidence quality for ntopng, not a production-path outage.

## GitHub repository access

The configured `origin` for this repository is
`git@github.com:Kingpro500/homelab-komodo.git`. Read access over SSH was
live-verified on 4 November 2026. A read check does not prove push access;
never test push by creating a throwaway commit. Use the configured GitHub
connector or an explicitly requested normal Git workflow when a write is
needed.

## Gitea network-map source and publication

Gitea at `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git` is exclusively
the authoritative source and publisher for the network map. The clean source
is on PC6/CT120 at `/opt/moved-services/nettkart-repo`; publication runs only
through `/usr/local/sbin/nettkart-publish`, which pushes, validates, archives,
and atomically replaces the live map. Gitea read/push and the publisher route
were live-verified on 6 November 2026. Never use this copy to deploy any other
homelab file.

## GitHub source boundary

GitHub (`git@github.com:Kingpro500/homelab-komodo.git`) is the source for all
non-network-map code, stacks, automation, and operational documentation.
Read access was live-verified on 6 November 2026. Do not mix GitHub changes
into the Gitea map publisher, and do not publish an unreviewed dirty worktree.

## Komodo control plane

Komodo Core is hosted on PC9/CT110 (`10.0.0.117:9120`). Use the managed
Proxmox SSH route for host/container diagnostics. No separate Codex-held
Komodo API credential is currently registered in the local secure-reference
catalog; do not infer the service is unavailable from that fact, and do not
invent or store a credential in this repository. Use the established Komodo
session or an explicitly documented credential reference when an authenticated
operation is requested.

**Verified local API route:** when an administrative Komodo action is requested,
run the request inside Core's trusted CT110 context. The local-login response
is wrapped: the bearer value is `data.jwt`, not a top-level `jwt` or `token`.
Pass that value unchanged as the `Authorization` header to the Core API. A
read-only `POST /read/ListRepos` with `{}` returned HTTP 200 on 6 November
2026. Keep the local admin values and the JWT in process-local variables only;
never print them, put them in a shell history, Git, NetBox, or this runbook.

For a new Komodo server, use the established public-key server registration
flow first. Do not create an onboarding key when the server already has an
accepted Periphery public key. After Periphery reports a successful Core login,
create and deploy application stacks through the Core API or UI from their
versioned GitHub source.

### Stack API procedure and checks

For a requested stack deployment, use the existing Komodo repository resource
and create the Stack through `POST /write/CreateStack`, then start it through
`POST /execute/DeployStack`. Keep all authentication values process-local.
The minimum stack configuration is the target `server_id`, the `linked_repo`,
the branch, `run_directory`, `file_paths`, and an explicit project name.

There are three implementation details that are easy to get wrong:

1. The local-login bearer is the `data.jwt` field and is passed unchanged in
   `Authorization`.
2. `GET /read/GetStack` serializes the database identifier as
   `_id["$oid"]`; `POST /write/UpdateStack` requires that inner text value as
   its `id`, not the JSON object.
3. `file_paths` are relative to the configured `run_directory`. For example,
   a repository source at `pc9-ct124-uisp/docker-compose.yml` with
   `run_directory: pc9-ct124-uisp` must use
   `file_paths: ["docker-compose.yml"]`.

Before declaring a deploy active, verify all of the following: the stack
reports no `info.missing_files` or `info.remote_errors`; the target has the
expected running container; and the service responds on its intended local
endpoint. A successful `DeployStack` acceptance only means Core queued the
operation, not that the service is ready. This procedure and the file-path
correction were verified while deploying UISP to `pc9-ct124-uisp` on
6 November 2026.

## Claude (Cowork) access route

Claude in the Claude desktop app (Cowork) reaches the homelab through a local
MCP server on Roger's Mac mini (`rogers-mac-mini-local`). Claude's own Cowork
Linux VM cannot reach the LAN: its egress proxy answers `10.0.0.0/24` and SSH
with `403 blocked-by-allowlist`, and the account egress setting does not
change that.

| Item | Value |
| --- | --- |
| MCP server | `homelab-ssh`, tool `ssh_run` |
| Server file | `~/.local/share/homelab-ssh-mcp/homelab-ssh-mcp.pl` on the Mac (core Perl and `/usr/bin/ssh`, no dependencies) |
| Registration | `~/Library/Application Support/Claude/claude_desktop_config.json` (`mcpServers.homelab-ssh`) |
| Source and installer | `~/Documents/claude-homelab/` (`install.sh` copies the server out of `~/Documents`, which macOS privacy protection blocks for Claude's child processes) |
| Targets | allowlisted in the server: `pc6` 10.0.0.120, `pve` 10.0.0.102, `pc9` 10.0.0.103; guests only through `pct exec` / `qm` |
| Identity | currently the shared deployment key `~/.ssh/codex_fleet_deploy` as `root`; a dedicated Claude key is planned so each agent can be revoked separately |
| Audit | every command and exit code is appended to `~/.local/share/homelab-ssh-mcp/ssh-audit.log` on the Mac |
| GitHub | working clone `/root/claude-work/homelab-komodo` on PC6 (HTTPS); token stored by Roger in `/root/.config/git/github-credentials` (mode `0600`, git `credential.helper store`) |

API credentials: Claude does not read the Mac's `~/.codex/secure/` files and
none are copied for it. OPNsense, UniFi and EdgeSwitch data come from the
secured material on Hermes CT130 (`/home/hermes/.hermes/.env`, `unifi.env`,
`edgeswitch.env`); NetBox from CT120. Values are never printed.

Live-verified 8 November 2026 (read-only): `hostname` on pc6, pve and pc9;
`pvecm status` quorate (pc1 offline); `pct exec 130` metrics on `:9130`;
`pct exec 120` Docker containers up; CT200 Emby `HTTP 200` on
`10.0.0.150:8096`; GitHub `git ls-remote` with the stored credential.
`git` was installed on PC6 from Debian packages for this route.

Claude follows the same rules as every other agent: read-only verification
first; changes, restarts, deploys and credential work only on an explicit
request; branch `agent/claude/<task>` and a pull request on GitHub for
repository changes.

## Facts merged from the former Gitea runbook copy

These were only in the Gitea copy (commits `1a1751f`, `248cbab`) and are kept
here so that copy can be retired:

- Hermes CT130 also holds secured EdgeSwitch material and runs a read-only
  collector for port health, errors/drops and PoE. It does not change switch
  configuration.
- Hermes' OPNsense route was re-verified on 6 November 2026 with the read-only
  `/api/core/system/status` call; `opnsense_status_sampler_up 1` confirmed the
  runtime sampler.
- Prometheus, rules, targets, alert state and Blackbox probes: PC9/CT104.
  Long-term observability data and correlation: ClickHouse on PC6/CT117.
- Stop rule: if the user says **stop**, terminate running work immediately and
  do not continue credential discovery or configuration changes.


## Network map and NetBox

Use this runbook for agent behaviour and access paths. Use the network map and
NetBox for topology, addresses, ownership, dependencies and service state.
Neither is a secret store. Add a link/reference here when a new management API
or diagnostic route is introduced.

## Updating this runbook

Update the relevant section in the same change that adds, removes, or moves a
management path. Include: system, preferred route, credential reference (not
the credential), permitted action level, and a safe verification method.
