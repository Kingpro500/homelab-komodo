# Homelab inventory

Proxmox guests across four nodes, what each one does, and where the naming is
wrong. Generated from the Proxmox API and Komodo; Proxmox guest names cannot be
changed from automation, so the "new name" column is a proposal.

## Nodes

| Node | Address | Role |
|---|---|---|
| pc8 (`pve`) | 10.0.0.102 | Proxmox master. Home Assistant, Komodo core, Pi-hole |
| pc6 | 10.0.0.120 | Workload host. Most guests, plus the Unraid VM |
| pc9 | 10.0.0.103 | Pi-hole, Emby backup, Periphery agent |
| pc1 | 10.0.0.112 | Dual boot with Windows. Ollama only |
| pc7 | 10.0.0.1 | OPNsense firewall, not a Proxmox node |

pc1 runs Windows several times a day for gaming. Anything that must stay up lives
on pc6, pc8 or pc9. n8n used to violate this; it moved to CT 103 on pc6.

## Guests

| Node | VM | Current name | IP | RAM | Disk | Docker | Stacks | Proposed name | Notes |
|---|---|---|---|---|---|---|---|---|---|
| pc1 | 156 lxc | `pc1-ct156-ollama` | 10.0.0.133 | 3G | 32G | yes | 1 | | Local LLM. **Runs on CPU**: no GPU is passed through, `/api/ps` is empty, and a short reply takes ~9 s |
| pc6 | 101 qemu | `Unraid-Tower` | 10.0.0.101 | 15G | — | no (VM) | 0 | | Docker in a VM. 31 of 32 containers stopped. **Holds the only GPU passthrough in the cluster** |
| pc6 | 103 lxc | `pc1-ct103-node` | 10.0.0.119 | 4G | 32G | yes | 2 | `pc6-ct103-node` | n8n and Open WebUI. **Names differ:** the Proxmox guest name and `hostname` in the LXC config are still `pc1-ct103-node`, but Periphery now reports `pc6-ct103-node`. That mismatch is what kept the server red; the agent was renamed, not the guest. Renaming the guest in Proxmox is still pending |
| pc6 | 104 lxc | **`pc6`** | 10.0.0.124 | 4G | 32G | yes | 1 | `pc6-ct104-media-downloaders` | MeTube, Pinchflat, MySpeed, DiskSpeed |
| pc6 | 109 lxc | **`pc6-ct109-node`** | 10.0.0.128 | 4G | 32G | yes | 12 | `pc6-ct109-docker` | Shared Docker node: arr stack, Grafana, Homepage, Kuma, Seerr, Speedtest, Deluge, Audiobookshelf, Grovemap, Glance, Dashy, Heimdall |
| pc6 | 111 lxc | `pc6-ct111-iventoy` | 10.0.0.134 | 1G | 16G | yes | 1 | | iVentoy PXE boot |
| pc6 | 151 lxc | **`emby-pc6`** | 10.0.0.150 | 8G | 256G | yes | 1 | `pc6-ct151-emby` | Active Emby. Transcoding should use the N355 iGPU |
| pc6 | 152 lxc | `pc6-ct152-roon` | 10.0.0.125 | 4G | 32G | yes | 1 | | Roon server. Source of the multicast noise behind the September ARP flapping |
| pc6 | 153 lxc | `pc6-ct153-immich` | 10.0.0.127 | 8G | 64G | yes | 1 | | Photo library |
| pc6 | 154 lxc | `pc6-ct154-paperless` | 10.0.0.131 | 4G | 64G | yes | 1 | | Documents and scanning |
| pc6 | 155 lxc | `pc6-ct155-unifi` | 10.0.0.132 | 2G | 16G | yes | 1 | | UniFi Network Controller |
| pc6 | 157 lxc | `pc6-ct157-hermes` | 10.0.0.135 | 4G | 32G | yes | 0 | | Hermes agent. Gateway, cron jobs, watchdogs. Runs no Komodo stacks |
| pc9 | 106 lxc | **`komodo-pc9`** | 10.0.0.122 | 4G | 16G | yes | 0 | `pc9-ct106-node` | Periphery agent, no stacks |
| pc9 | 108 lxc | **`docker-test`** | 10.0.0.130 | 1G | 8G | yes | 0 | *delete* | **Unused.** No stacks, not in Homepage, not mentioned anywhere. 1 GB RAM for nothing |
| pc9 | 116 lxc | `pihole-pc9` | 10.0.0.116 | 1G | 8G | yes | 1 | | Pi-hole DNS, upstream Unbound |
| pve | 100 qemu | `homeassistant` | 10.0.0.7 | 9G | — | no (VM) | 0 | | Home Assistant, a VM not a container. 1834 entities |
| pve | 102 lxc | **`Komodo-core`** | 10.0.0.117 | 1G | 36G | yes | 1 | `pc8-ct102-core` | Komodo API and FerretDB |
| pve | 110 lxc | `pc8-ct110-node` | 10.0.0.129 | 2G | 16G | yes | 0 | | Periphery agent, no stacks |
| pve | 115 lxc | `pihole-pc8` | 10.0.0.115 | 1G | 8G | yes | 1 | | Pi-hole DNS, upstream Unbound |

Every guest has an empty Proxmox description. The Komodo server descriptions
carry the same information and are filled in.

## GPU

The only GPU passthrough in the cluster is in the Unraid VM on pc6:
`0000:00:14`, `0000:06:00.0`, `0000:07:00.0`. Proxmox does not report device
names, so which one is the iGPU has to be checked with `lspci` from inside the VM.

CT 156 on pc1 has no `hostpci` entry at all, and pc1 exposes no PCI GPU. Its
Ollama therefore runs on the CPU. Giving the Unraid VM's GPU to CT 156 does not
help, because they are different physical hosts. Either pass pc1's own card
through to CT 156, or run Ollama in Unraid where a GPU is already present.

Emby should transcode on the N355 iGPU. That means moving the iGPU passthrough
from the Unraid VM to CT 151 on the same host, which is possible but takes the
card away from Unraid.

## DNS chain

```
client -> Pi-hole (10.0.0.115 / .116) -> Unbound (10.0.0.1) -> internet
```

Kea hands clients both Pi-hole addresses plus `94.140.14.14` as fallback. Unbound
holds 11 host overrides under `lan.local`, which is also the search domain Kea
hands out. The domain string must match on both sides or local names fail
silently.

Two Periphery agents, CT 110 and CT 106, carry no stacks. They are harmless but
also unused.
