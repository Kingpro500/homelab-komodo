# Proxmox → Komodo → GitHub live-audit

**Tidspunkt:** 2026-11-12 UTC  
**Metode:** Proxmox cluster inventory + Komodo `ListServers`/`ListStacks`/`GetStack` + GitHub `main`. Read-only audit; no live server or stack mutation.

## Sammendrag

- Komodo-servere: **50** (`Ok`: 28, `NotOk`: 20, `Disabled`: 2)
- Komodo-stacks kontrollert med `GetStack`: **50**
- Stacks med `remote_errors`, manglende serverkobling eller manglende filer: **5**

## Servere som krever separat vurdering

- `pc1-ct102-pihole` — `NotOk` — `6adb91e7f00623ce1f26cc08`
- `pc1-ct144-ct144` — `NotOk` — `6af4b28bb634dc32d227e744`
- `pc1-ct144-flux2` — `NotOk` — `6af46a15b634dc32d227dc0a`
- `pc1-ct145-darkbeast` — `NotOk` — `6af49297b634dc32d227e21f`
- `pc1-ct146-comfyui` — `NotOk` — `6af49297b634dc32d227e222`
- `pc1-ct147-ct147` — `NotOk` — `6af49297b634dc32d227e225`
- `pc1-ct148-ct148` — `NotOk` — `6af48881b634dc32d227e071`
- `pc1-ct149-ct149` — `NotOk` — `6af4ad15b634dc32d227e64b`
- `pc1-ct151-ct151` — `NotOk` — `6af4aee4b634dc32d227e6b1`
- `pc1-ct152-ct152` — `NotOk` — `6af49297b634dc32d227e22b`
- `pc1-ct153-ct153` — `NotOk` — `6af492afb634dc32d227e230`
- `pc1-ct156-ollama` — `NotOk` — `6af05c7c18171b583cde2eb3`
- `pc6-ct111-iventoy` — `NotOk` — `6af0539018171b583cde2d83`
- `pc6-ct119-spare` — `NotOk` — `6aeb85741862e512d2c7dff2`
- `pc6-ct130-hermes` — `Disabled` — `6ae2d3d34636d7b900f62d9d`
- `pc6-ct140-iventoy` — `NotOk` — `6ae0de6d4636d7b900f457ee`
- `pc6-ct150-browsers` — `NotOk` — `6ae0cf464636d7b900f44550`
- `pc6-ct151-emby` — `Disabled` — `6af0539018171b583cde2d85`
- `pc6-ct153-immich` — `NotOk` — `6af0539018171b583cde2d87`
- `pc6-ct154-paperless` — `NotOk` — `6af0539018171b583cde2d89`
- `pc6-ct215-tubearchivist` — `NotOk` — `6af0539018171b583cde2d8b`
- `pc6-ct330-personal-services` — `NotOk` — `6af0539018171b583cde2d8d`

## Stack-avvik

- `ct118-gitea` — repo `Kingpro500/ct118-gitea`, branch `main`, server `pc6-ct118-gitea` — Failed at: Clone Repo: fatal: unable to access 'http://Gitea/Kingpro500/ct118-gitea/': Failed to connect to Gitea port 80 after 493 ms: Could not connect to server
- `pc6-ct103-open-webui` — repo `Kingpro500/homelab-komodo`, branch `main`, server `6abdec74478bbf9f98ef3ca3` — missing/invalid metadata
- `pc6-ct109-ansible-semaphore` — repo `Kingpro500/homelab-komodo`, branch `codex/ct109-semaphore-ct117-clickhouse`, server `pc6-ct109-semaphore` — Failed at: Clone Repo: fatal: Remote branch codex/ct109-semaphore-ct117-clickhouse not found in upstream origin
- `pc6-ct117-clickhouse` — repo `Kingpro500/homelab-komodo`, branch `codex/ct109-semaphore-ct117-clickhouse`, server `pc6-ct117-clickhouse` — Failed at: Clone Repo: fatal: Remote branch codex/ct109-semaphore-ct117-clickhouse not found in upstream origin
- `pc6-ct152-roon` — repo `Kingpro500/homelab-komodo`, branch `main`, server `6abd2c9277bd16d560d9ddfb` — missing/invalid metadata

## Navn/server/run-directory som ikke samsvarer åpenbart

- `ct112-ntp` → server `pc7-ct112-ntp`; run directory ``
- `ct118-gitea` → server `pc6-ct118-gitea`; run directory ``
- `pc6-ct109-grovemap` → server `pc6-ct340-krusader`; run directory `pc6-ct109-grovemap`
- `pc6-ct115-unifi` → server `pc7-ct115-unifi`; run directory `pc6-ct155-unifi`
- `pc6-ct120-netbox` → server `pc6-ct120-monitoring`; run directory `stacks/pc8-ct102-netbox`
- `pc6-ct120-network-tests` → server `pc6-ct120-monitoring`; run directory `pc6-ct104-network-tests`
- `pc6-ct120-stepca` → server `pc6-ct120-monitoring`; run directory `stacks/pc8-ct102-stepca`
- `pc6-ct120-web` → server `pc6-ct120-monitoring`; run directory `pc6-ct109-web`
- `pc6-ct123-metube` → server `pc6-ct123-ct123`; run directory `pc6-ct104-media-downloaders`
- `pc6-ct143-crafty` → server `pc6-ct143-ct143`; run directory `pc6-ct143-crafty`
- `pc6-ct200-emby` → server `pc6-ct200-emby`; run directory `pc6-ct151-emby`

## Godkjent neste steg

- Ikke slett, omregistrer eller deploy disse objektene som masseoperasjon.
- For hvert avvik: identifiser faktisk CT/IP/Periphery og tiltenkt compose-katalog; korriger deretter én server/stack om gangen med read-back.
- Før eventuell lagringsopprydding på pc7: ta backup og frigjør plass kun etter eksplisitt valg av trygge objekter; ikke slett gjestedisker blindt.
- Emby-relaterte objekter må behandles med aktiv-stream-sjekk og uten restart under avspilling.

## Ny kontroll: pc7-lagring og fysisk CT-inventar

- `pc7/local-lvm` er `90.34 %` brukt; thin-pool `data` har `5.46 GiB` ledig og `2.98 %` metadata brukt.
- Ingen LXC-snapshots ble funnet i `/etc/pve/lxc/*.conf` ved kontrollen.
- Det skal ikke slettes virtuelle disker eller snapshots som «opprydding» uten å identifisere eier og ta backup.
- Fysisk inventar bekrefter at `pc7-ct115-unifi` og `pc7-ct152` faktisk finnes på pc7, mens `pc6-ct123` og `pc6-ct200-emby` faktisk finnes på pc6.
- Dette endrer ikke avvikene: `pc6-ct115-unifi` er fortsatt en feil/misvisende Komodo-stack når den peker på server `pc7-ct115-unifi` og run directory `pc6-ct155-unifi`; `pc6-ct123-metube` bruker fortsatt `pc6-ct104-media-downloaders`; `pc6-ct200-emby` bruker fortsatt `pc6-ct151-emby` som run directory.

## Status

Dette er fortsatt en read-only revisjon. Ingen Komodo-servere, stacks, Proxmox-konfigurasjoner eller disker er endret.
