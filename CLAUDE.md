# Instruksjoner for Claude

## 🚨 Start HVER økt med disse to sjekkene

### 1. Drift-vakten — rydd før du bygger nytt

Les `http://10.0.0.135:9118/drift`, eller se toppen av nettverkskartet http://10.0.0.124:3020/.

- `level` er `kritisk` eller `advarsel`: **rydd opp i listen først.** Deploy/publiser det som er merget, og fullfør eller lukk åpne PR-er. **Ikke legg nye commits eller PR-er oppå.** Rutine: [pc7-ct130-hermes/drift-vakt/README.md](pc7-ct130-hermes/drift-vakt/README.md).
- Ingenting skal stoppe opp: kan du ikke rydde, skriv det øverst i svaret til Roger.
- Én oppgave = én gren `agent/<agent>/<oppgave>` = én PR = merge **og** deploy/publiser i samme runde.

### 2. GitHub-tilgang — den finnes. Si aldri «mistet tilgang» før du har prøvd rutene under

Din egen sandkasse (Codex cloud, Claude Cowork o.l.) kan mangle `gh`-login eller ha et ugyldig `GH_TOKEN`. **Det betyr ikke at homelab-ets GitHub-tilgang er borte.** Bruk de faste rutene:

| Behov | Fast rute | Sjekk (kun lesing) |
| --- | --- | --- |
| git lese/push | SSH til pc6 (`10.0.0.120`), klonen `/root/claude-work/homelab-komodo` med deploy-nøkkel `/root/.ssh/claude_github_deploy` (satt i `core.sshCommand`) | `cd /root/claude-work/homelab-komodo && git fetch origin && git log -1 --oneline origin/main` |
| PR/merge (API) | Hermes CT130 på **pc7** (`10.0.0.107`), `GITHUB_TOKEN` i `/home/hermes/.hermes/.env`. Fra pc6: `ssh root@10.0.0.107 'pct exec 130 -- …'` | `GET https://api.github.com/repos/Kingpro500/homelab-komodo` med tokenet → 200 |
| PR/merge (reserve) | Fine-grained token på pc8: `/root/.config/claude/github.env` | samme |
| Codex | `git@github.com:Kingpro500/homelab-komodo.git` med Codex sin egen SSH-identitet (se ACCESS-RUNBOOK) | `git ls-remote origin HEAD` |

Drift-vakten tester GitHub-API-et hvert 15. minutt. `github_access.ok: true` i `/drift` betyr at tilgangen virker, og at feilen ligger i din egen sandkasse. Rapporter **ruten som feilet og den nøyaktige feilmeldingen**, aldri bare «ingen tilgang». Aldri vis, kopier eller committ tokenverdier. Mer: [docs/network-map/ACCESS-RUNBOOK.md](docs/network-map/ACCESS-RUNBOOK.md).

Før arbeid i pc6-klonen: `git switch main && git pull --ff-only`.


Les også [AGENTS.md](AGENTS.md) – den har åpne saker (bl.a. Homepage på pause).

## ⚠️ Nettverkskartet ligger IKKE i GitHub

**Nettverkskartet (`docs/network-map/`) redigeres og publiseres kun via Gitea på CT120.**

- Kilde: `CT120:/opt/moved-services/nettkart-repo/docs/network-map/nettverkskart.html` (origin = Gitea `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git`, CT118).
- Publisering: kjør `/usr/local/sbin/nettkart-publish` på CT120 etter commit. Skriptet pusher til Gitea, validerer versjon + endringsnotat og publiserer atomisk.
- Gjeldende regler: `PUBLISHING.md` i Gitea-kopien (samme mappe på CT120).
- Kopien av `docs/network-map/` i **dette GitHub-repoet er utdatert og brukes ikke**. Ikke rediger den, ikke publiser fra den, og ikke deploy kartet med Komodo/GitHub.
- Alt annet (Komodo-stacker, Homepage, Dashy, Ansible, kode, øvrig dokumentasjon) ligger i **GitHub**.
