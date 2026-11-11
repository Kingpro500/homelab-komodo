# pc1 / CT144 (ct144-flux2) – FLUX.2 klein 4B (lokal bildegenerering)

Ikke en Docker-stack: systemd-tjeneste `flux` i CT144 (Debian 13), venv `/opt/flux/venv` (torch cu128 + diffusers fra git).
- Web: http://10.0.0.219:7860 (enkel prompt-side, `POST /gen`). Ingen autentisering, kun LAN.
- Modell: `/models/FLUX.2-klein-4B` (CT) = NFS `Tower-isos/flux-models` (15 GB, Apache-2.0, ikke gated). Offline (`HF_HUB_OFFLINE=1`).
- GPU: RTX 3070 8 GB delt med pc1. To moduser i samme tjeneste (lastes ved behov, bare én om gangen, bytte ~1–2 min første gang):
  - **Kjapp**: transformer + tekstenkoder i 4-bit (bitsandbytes nf4), helt på GPU (~7,6 GB VRAM). ~4 s/bilde 768², 4 steg.
  - **Oppgrader**: full bf16 med `enable_sequential_cpu_offload()`, ~2 min/bilde 1024². Bruk samme prompt og seed som utkastet.
  RAM 12 GB trengs. Ingen ekstra CT: GPU-en er den samme.
- CT144-endringer: rootfs 8→20 GB, 12 GB RAM, 2 GB swap, 6 kjerner, mp0 `/models`, nvidia-devicer (195/510) og bind av host `libcuda`/`libnvidia-ml` 615.71.09. Oppdateres driveren på pc1 må de to mount-linjene i `/etc/pve/lxc/144.conf` og symlinkene i CT oppdateres.
- Backup av gammel config: `/root/144.conf.bak-2026-11-11` på pc1.
- FLUX.2 Dev (32B) er ikke installert: krever ~64 GB bf16 + gated HF-lisens og > 16 GB RAM.
- Bruker GPU: stopp `flux` (`systemctl stop flux`) før CT350 (ollama) brukes.

## Lagring, galleri, kø (v2)
- Standard 1920x1080 (høyde rundes til 1072, må være delbar på 16). Maks 2048.
- Alle bilder lagres som PNG + JSON (prompt, seed, steg, modus) i `/models/output` = Tower-isos/flux-models/output, miniatyrer i `thumbs/`.
- Jobbkø (`/submit`, `/status`): én jobb om gangen, køen vises på siden. Køen ligger i minnet og tømmes ved restart av `flux`.
- Galleri på forsiden: Oppgrader (samme prompt/seed i full modell), Bruk prompt, Slett (`DELETE /img/<navn>`, fjerner PNG, JSON og miniatyr).
- Ingen innlogging: alle på LAN kan slette.
- Kjapp-modellen forhåndslastes i bakgrunnen ved oppstart (ca. 2–4 min før første bilde er raskt).
