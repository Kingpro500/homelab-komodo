# NetBox – opprett nye Proxmox-CT-er

- Aktiv n8n-flyt ID: `VhwISm6PTWWraqo2`. Kjøres hver time; også testet med webhook (fjernet før planlagt drift).
- Les Proxmox `/api2/json/cluster/resources?type=vm` med n8n-credential «Proxmox inventory read (n8n)».
- Les NetBox `/api/virtualization/virtual-machines/?limit=1000` med n8n-credential «NetBox VM create v2 (n8n)». Stopp uten skriving hvis svaret er ufullstendig/paginert.
- Sammenlign **VMID**, ikke bare navn (NetBox har gamle nodeprefikser). Opprett kun LXC med VMID ≥ 144, gyldig `ctNNN-navn`/`pcN-ctNNN-navn`, komplett navn/ressurser, og status running/stopped. Hopp over `-tom`, utilgjengelige gjester og allerede registrerte VMID-er. Opprett VM med cluster CyberCluster (1), site Homelab (1), status, CPU/minne/disk; eksisterende VM-er endres ikke.
- **Begrensning:** IP/interface registreres ikke. Proxmox cluster/resources inneholder ikke IP. Noden har kun NetBox VM view/add, ikke delete/change/IP-tilgang. Gjentatte kjøringer oppretter ikke samme VMID på nytt.
- CT144/CT145 er foreløpig ikke registrert fordi pc1 er bootet til Windows og Proxmox kun returnerer `vmid`/`unknown` uten navn/ressurser. Når pc1 igjen er tilgjengelig og API-et returnerer komplette data, tar neste kjøring dem inn hvis de har gyldige navn.
- Håndtering ved feil: n8n lagrer både vellykkede og mislykkede executions. Ingen automatisk push er konfigurert; kontroller kjøringene etter feil. NetBox-tokenet ligger bare i n8n credential, aldri i repoet.

## Verifisert
- Dry-run: Proxmox og NetBox n8n-credentials ble testet med ekte API-responser.
- n8n opprettet `pc9-ct203-emby-standby` som NetBox VM ID 48; felt og status ble lest tilbake i Django. Andre kjøring ga ingen duplikat (ingen kandidat for 203). Endelig tidsstyrt graf er aktiv og lest tilbake; selve timeutløsningen er ennå ikke observert.
- pc6 `netbox-proxmox-sync` oppdaterer status/disk på eksisterende VM-er og er ikke endret.
