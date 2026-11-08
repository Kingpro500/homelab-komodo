# Instruksjoner for Claude

Les også [AGENTS.md](AGENTS.md).

## ⚠️ Nettverkskartet ligger IKKE i GitHub

**Nettverkskartet (`docs/network-map/`) redigeres og publiseres kun via Gitea på CT120.**

- Kilde: `CT120:/opt/moved-services/nettkart-repo/docs/network-map/nettverkskart.html` (origin = Gitea `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git`, CT118).
- Publisering: kjør `/usr/local/sbin/nettkart-publish` på CT120 etter commit. Skriptet pusher til Gitea, validerer versjon + endringsnotat og publiserer atomisk.
- Gjeldende regler: `PUBLISHING.md` i Gitea-kopien (samme mappe på CT120).
- Kopien av `docs/network-map/` i **dette GitHub-repoet er utdatert og brukes ikke**. Ikke rediger den, ikke publiser fra den, og ikke deploy kartet med Komodo/GitHub.
- Alt annet (Komodo-stacker, Homepage, Dashy, Ansible, kode, øvrig dokumentasjon) ligger i **GitHub**.
