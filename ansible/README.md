# Ansible for CyberCluster (Proxmox)

Ansible-kontrollpunkt mot Proxmox-clusteret **CyberCluster**, ved hjelp av
API-token (`hermes@pve!monitor`) — **ingenting installeres på nodene**
(agentless), og brukeren er read-only (PVEAuditor).

Kjøres fra `pc6-ct157-hermes` (10.0.0.135).

## Forutsetninger

- `ansible-core` + `community.proxmox` installert.
  ```sh
  python3 -m pip install --user --break-system-packages ansible-core 'proxmoxer>=2.0'
  ansible-galaxy collection install community.proxmox
  ```
- Proxmox-credentials i miljøet (fra `~/.hermes/.env`) — se `.env.example`.

## Struktur

```
ansible/
├── ansible.cfg              # peker på inventory + collections
├── inventory/proxmox.yml    # de fire nodene gruppert (ansible_connection: local)
├── inventory/group_vars/all.yml  # API-adresse + token-referanser (fra env)
├── playbooks/
│   └── cluster_status.yml   # read-only diagnose-playbook
└── .env.example
```

Merk: `group_vars/` ligger **under `inventory/`** — det er der Ansible
oppdager den uansett hvilken playbook/mappe du kjører fra (en rot-plassert
`group_vars/` ble funnet av ad-hoc-kommandoer men ikke av playbooks i
`playbooks/`, noe som kostet debug-tid).

## Bruk

```sh
cd ansible
# Hele clusteret
ansible-playbook -i inventory/proxmox.yml playbooks/cluster_status.yml

# Kun én node
ansible-playbook -i inventory/proxmox.yml playbooks/cluster_status.yml -e target=pve
```

Nodene er lokalisert med `ansible_host` og nås over API-et (HTTP 8006),
ikke SSH. `community.proxmox`-modulene bruker tokenet direkte.
