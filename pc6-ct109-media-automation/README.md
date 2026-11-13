# Media automation on pc6 CT 109

One Komodo stack on the shared Docker node `pc6-ct109-node` (`10.0.0.128`).
It contains Bazarr, Prowlarr, Sonarr, Radarr, Readarr and Podgrab.

| Service | Address |
| --- | --- |
| Bazarr | `http://10.0.0.128:6767` |
| Prowlarr | `http://10.0.0.128:9696` |
| Sonarr | `http://10.0.0.128:8989` |
| Radarr | `http://10.0.0.128:7878` |
| Readarr | `http://10.0.0.128:8787` |
| Podgrab | `http://10.0.0.128:8081` |

Runtime configuration is copied from Tower to `/opt/media-automation`; media
and downloads stay on Tower. The CT has a dedicated RW bind mount at `/data`,
which maps to Tower's `media` share. Audiobookshelf remains separate within the
same CT and uses its existing read-only `/scan/media` bind mount.

Required Komodo variable:

```text
MEDIA_AUTOMATION_CONFIG_ROOT=/opt/media-automation
```

## 13. november 2026 — CT210 oppgradert til Debian 13 (trixie)

Hele CT210 (`pc6-ct210-multi-medietjenester`, Komodo-server `pc6-ct109-node`,
10.0.0.128) ble oppgradert fra Debian 12 bookworm til Debian 13 trixie på
stedet. Grunnen var at CT-en satt fast på Docker 20.10.24 med bare
`docker-compose` 1.29.2; `docker-compose-v2` finnes ikke i bookworm.

CT-en ble **oppgradert, ikke flyttet**, med vilje: alt det vanskelige ved den
ligger i CT-konfigurasjonen, ikke i Docker — de fire bind-mountene fra Tower
(`/scan/media`, `/scan/photos`, `/scan/backups`, `/data`), GPU-en
`/dev/dri/renderD128`, `/dev/net/tun` til deluge sin VPN, 7 kjerner og IP-en.
En flytting ville betydd å gjenskape alt dette og 14 GB state for 13 containere.

| | Før | Etter |
|---|---|---|
| OS | Debian 12.15 bookworm | Debian 13.7 trixie |
| Docker | 20.10.24 | 26.1.5 |
| Compose | `docker-compose` 1.29.2 | `docker compose` 2.26.1 |

**Angrefrist:** Proxmox nekter vanlig snapshot av denne CT-en fordi den har
bind-mounts fra Tower. Det ble derfor tatt et LVM-thin-snapshot av rootfs med
CT-en stoppet, slik at det er konsistent:

```sh
# finnes på pc6:
lvs -o lv_name,origin pve | grep 210
#   vm-210-disk-0-pre-trixie  vm-210-disk-0

# tilbakerulling (CT må være stoppet):
pct stop 210
lvremove pve/vm-210-disk-0
lvrename pve/vm-210-disk-0-pre-trixie pve/vm-210-disk-0
pct start 210
```

Snapshotet opptar plass i thin-poolen så lenge det ligger der. Slett det med
`lvremove pve/vm-210-disk-0-pre-trixie` når oppgraderingen har stått en stund.

**To ting å vite hvis dette gjøres igjen:**

1. Dist-upgraden ble startet med `systemd-run`, og da systemd selv ble byttet
   ut mistet jobben sin egen enhetsfil og stoppet midt i. `dpkg --audit` var
   like fullt ren, og resten gikk gjennom i andre forsøk. Sjekk alltid
   `dpkg --audit` og `apt-get check` etterpå før du konkluderer.
2. Containerne ble stoppet med `docker stop` før oppgraderingen. De har
   `restart=unless-stopped`, som betyr at de **ikke** kommer tilbake av seg
   selv etter en manuell stopp — de må startes igjen med `docker start`.
   Etterpå viste Komodo dem fortsatt som *exited* i flere minutter; container-
   listen i Core er et hurtiglager. En `docker restart komodo-periphery` i
   CT-en oppdaterte den med én gang.
