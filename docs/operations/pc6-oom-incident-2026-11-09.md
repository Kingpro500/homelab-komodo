# PC6 minnekollaps 2026-11-09

## Hva skjedde

- PC6 (Proxmox, 31 GiB RAM) hang fra ca. 03:30 og var helt utilgjengelig til den ble strømrestartet 06:12. Kjernen svarte på ping, men SSH, Proxmox-API og alle gjester sto.
- Journal fra forrige boot: `Under memory pressure` fra 2026-11-08 21:46, helsesjekker timeout fra 02:40, `blocked for more than 122 seconds` fra 03:24, siste logglinje 03:46.
- `pc6-resource-guard` slo ikke inn. `media_recovery.py` forsøkte `pct reboot 250` kl. 03:05, som timet ut etter 100 s.

## Rotårsak

Minneovertegning. Unraid-VM 201 har fast 12 GiB (balloon av), mens kjørende CT-er hadde til sammen 58 GiB `memory`-tak på en vert med 31 GiB. Swap (8 GiB) var full allerede 2026-11-08 kl. 12:55.

Medvirkende:

1. `media_recovery.py` åpnet en ekte HLS-strøm på Tunarr kanal 1 hvert 5. minutt. Det holdt en ffmpeg-transkoding (VAAPI, kilde Emby) i gang kontinuerlig uten seere. Rettet 2026-11-08: sjekken leser nå bare `/api/channels` og `/web/`.
2. Masse-oppstart av 15 CT-er 2026-11-08 12:50 (root@pam), inkludert arkiv-CT-er. Kilde ikke fastslått.
3. En hengende `hermes model`-prosess i CT130 (uten TTY) brukte 100 % av én kjerne. Drept 2026-11-08.

## Tiltak gjort

| Tid | Tiltak |
| --- | --- |
| 11-08 | Drept hengende `hermes model` (CT130) |
| 11-08 | CT105 `memory` 2048 → 4096, `swap` 512 → 1024 |
| 11-08 | `media_recovery.py`: Tunarr-sjekk uten HLS-strøm (pc6 og pc9). Backup: `/usr/local/sbin/media_recovery.py.bak-20261108` |
| 11-09 | CT215 stoppet og `onboot: 0` |
| 11-09 | Alle CT-er på PC6 stoppet. Liste: `/root/ct-running-before-stop-20261109.txt` |
| 11-09 | Alle CT-er og VM 201 på PC6 satt til `onboot: 0`. Tidligere verdier: `/root/onboot-before-20261109.txt` |
| 11-09 | CT112 (ntp, 10.0.0.170) migrert PC6 → PC7, rootfs `local:raw` → `local-lvm`, `onboot: 1` |

## Merknad: ext4 MMP på raw-images

CT-er med rootfs som `.raw` på `local` (dir) har ext4 `mmp` aktivert (check interval 300 s). Etter ukontrollert stopp venter `mount` ca. 12 minutter før CT-en starter, og `pve-guests` blokkerer imens resten av oppstarten. Flytt til `local-lvm` ved migrering.

## Videre plan

Tjenester flyttes fra PC6 til andre noder. PC6 skal ikke starte gjester automatisk før summen av minnetak passer verten.
