# Instruksjoner for AI-agenter (Codex, Claude, Hermes)

## ⏸️ Status: Homepage-arbeid på PAUSE (8. nov 2026)

Brukeren har bevisst satt Homepage-arbeidet på pause. Ikke redeploy Homepage før brukeren tar opp saken igjen.

- Merget i GitHub, men **ikke deployet**: PR #78 (`13d44c2`) – pve→pc8, ny pc7-flis, Home Assistant på pc9, Netdata pc8, Pi-hole CT101 pc6, OPNsense VM191 (pc7) / VM190 (pc8). Gjelder `homepage/config/services.yaml`, `homepage/services.runtime.yaml`, `pc6-ct109-dashy/config/conf.yml`.
- Komodo-stacken `pc6-ct120-homepage`: `latest_hash` står fortsatt på `d0c904a`, `deployed_hash` på `f84c1c5`. PullStack er kjørt, men årsaken til at hashen ikke oppdateres er **ikke undersøkt**.
- Neste steg: les Komodo-oppdateringsloggen for PullStack på `pc6-ct120-homepage`, rett årsaken, deploy, verifiser `deployed_hash == latest_hash` og at http://10.0.0.124:3009 viser pc7/pc8.
- Samme status er ført i nettverkskartet (Gitea/CT120) som «Planlagt v2.155».


## ⚠️ Nettverkskartet ligger IKKE i GitHub

**Nettverkskartet (`docs/network-map/`) redigeres og publiseres kun via Gitea på CT120.**

- Kilde: `CT120:/opt/moved-services/nettkart-repo/docs/network-map/nettverkskart.html` (origin = Gitea `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git`, CT118).
- Publisering: kjør `/usr/local/sbin/nettkart-publish` på CT120 etter commit. Skriptet pusher til Gitea, validerer versjon + endringsnotat og publiserer atomisk.
- Gjeldende regler: `PUBLISHING.md` i Gitea-kopien (samme mappe på CT120).
- Kopien av `docs/network-map/` i **dette GitHub-repoet er utdatert og brukes ikke**. Ikke rediger den, ikke publiser fra den, og ikke deploy kartet med Komodo/GitHub.
- Alt annet (Komodo-stacker, Homepage, Dashy, Ansible, kode, øvrig dokumentasjon) ligger i **GitHub**.
