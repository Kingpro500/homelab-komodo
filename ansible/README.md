# Ansible for CyberCluster (Proxmox)

Ansible-kontrollpunkt mot Proxmox-clusteret **CyberCluster**. To lag:

1. **Read-only** — over Proxmox API-token (`hermes@pve!monitor`, PVEAuditor).
   Ingenting installeres på nodene (agentless).
2. **Operasjonelt (write)** — over SSH som root + `pct exec` for deploy og
   driftsrapport. Rot-nøkkelen gir kontroll; bruk kun til godkjente oppgaver.

Kjøres fra `pc6-ct157-hermes` (10.0.0.135).

## Forutsetninger

- `ansible-core` + `community.proxmox` installert.
  ```sh
  python3 -m pip install --user --break-system-packages ansible-core 'proxmoxer>=2.0'
  ansible-galaxy collection install community.proxmox
  ```
- Read-only: Proxmox-credentials i miljøet (fra `~/.hermes/.env`) — se `.env.example`.
- Operasjonelt: SSH-nøkkel `~/.ssh/id_ed25519_hermes` (root) mot nodene.

## Struktur

```
ansible/
├── ansible.cfg                 # peker på inventory + collections
├── inventory/proxmox.yml       # 4 noder (API, ansible_connection: local)
├── inventory/group_vars/all.yml  # API-adresse + token-referanser (fra env)
├── inventory/ssh.yml           # 4 noder (SSH root, for deploy/driftsrapport)
├── scripts/
│   ├── deploy-stack.sh         # deploy/oppdater én stack INNE i en CT
│   └── drift-info.sh           # samler driftsstatus INNE i en CT
├── playbooks/
│   ├── cluster_status.yml      # read-only: cluster, VM/CT, node, storage (API)
│   ├── deploy_stack.yml        # deploy/oppdater Docker-stack i én CT (SSH)
│   └── driftsrapport.yml       # driftsstatus fra alle CT-er (SSH)
└── .env.example
```

Merk: `group_vars/` ligger **under `inventory/`** — det er der Ansible
oppdager den uansett hvilken playbook/mappe du kjører fra (en rot-plassert
`group_vars/` ble funnet av ad-hoc-kommandoer men ikke av playbooks i
`playbooks/`, noe som kostet debug-tid).

## Bruk

```sh
cd ansible
# 1) Read-only clusterstatus (API-token)
ansible-playbook -i inventory/proxmox.yml playbooks/cluster_status.yml
ansible-playbook -i inventory/proxmox.yml playbooks/cluster_status.yml -e target=pve

# 2) Driftsrapport fra alle CT-er (SSH, read-only)
ansible-playbook -i inventory/ssh.yml playbooks/driftsrapport.yml
ansible-playbook -i inventory/ssh.yml playbooks/driftsrapport.yml --limit pc6

# 3) Deploy/oppdater én Docker-stack (SSH, WRITE)
ansible-playbook -i inventory/ssh.yml playbooks/deploy_stack.yml \
  -e node=pc6 -e ct=109 \
  -e stack_dir=/opt/komodo/stacks/pc6-ct109-homepage/pc6-ct109-homepage

# Tørrkjøring (validerer kun, ingen endringer):
#   ... -e dry_run=true
# Tving compose-kommando (v1-CT-er):  ... -e compose_cmd=docker-compose
```

**Deploy-stien gjør:** `git pull` (hvis repo) → `compose config -q` (valider)
→ `compose pull` → `compose up -d`. Skriptet kjøres INNE i CT-en (pct-push
+ `pct exec`), aldri inline — `pct exec` forkaster shell-quoting, så
komplekse kommandoer må ligge i en scriptfil.

