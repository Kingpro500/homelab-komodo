# Instruksjoner for AI-agenter (Codex, Claude, Hermes)

## 🚨 Start HVER økt med disse to sjekkene

### ⛔ Kan du ikke publisere, merge eller deploye? Si det tydelig, og meld det

Gjelder alle agenter og alle steder: GitHub (PR/merge), Komodo (deploy), Gitea/nettverkskartet (`nettkart-publish`) og alt annet som skal ut i drift.

1. **Prøv de dokumenterte rutene først** (se Tilgang under og `docs/ACCESS-RUNBOOK.md`). En feilende `gh`/`GH_TOKEN` i din egen sandkasse betyr ikke at tilgangen mangler.
2. **Når det likevel ikke går, skal svaret til Roger begynne med** `⛔ KAN IKKE PUBLISERE:` etterfulgt av hva det gjelder, hvilken rute du prøvde, og den nøyaktige feilmeldingen. Ikke gjem det nederst i svaret.
3. **Meld det i drift-vakten med en gang**, fra pc6 (homelab-ssh) eller CT120:
   ```sh
   homelab-blokkert meld "<hva>" "<rute prøvd>" "<nøyaktig feil>" --av <agent>
   ```
   Saken blir kritisk øverst i nettverkskartet og på telefonen til den er løst, også om du stopper eller økten avsluttes.
4. **Skriv aldri «ferdig», «publisert» eller «deployet»** om noe som bare er committet eller pushet til en gren.
5. Når det er fikset: `homelab-blokkert løst <id> "<hvordan>"`. Åpne saker: `homelab-blokkert liste`.

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

Drift-vakten tester GitHub-API-et hvert 15. minutt. `github_access.ok: true` i `/drift` betyr at tilgangen virker, og at feilen ligger i din egen sandkasse. Rapporter **ruten som feilet og den nøyaktige feilmeldingen**, aldri bare «ingen tilgang». Aldri vis, kopier eller committ tokenverdier. Mer: [docs/ACCESS-RUNBOOK.md](docs/ACCESS-RUNBOOK.md).

Før arbeid i pc6-klonen: `git switch main && git pull --ff-only`.


## ⏸️ Status: Homepage- og Dashy-arbeid på PAUSE (8. nov 2026)

Brukeren har bevisst satt Homepage- og Dashy-arbeidet på pause. Ikke redeploy Homepage eller Dashy før brukeren tar opp saken igjen.
- Dashy: Komodo-stacken `pc6-ct109-dashy` (status unknown) er ikke deployet med endringen i `pc6-ct109-dashy/config/conf.yml` fra #78 (ny flis pc7, pc8 som OPNsense-reserve). Kartet: «Planlagt v2.156».

- Merget i GitHub, men **ikke deployet**: PR #78 (`13d44c2`) – pve→pc8, ny pc7-flis, Home Assistant på pc9, Netdata pc8, Pi-hole CT101 pc6, OPNsense VM191 (pc7) / VM190 (pc8). Gjelder `homepage/config/services.yaml`, `homepage/services.runtime.yaml`, `pc6-ct109-dashy/config/conf.yml`.
- Komodo-stacken `pc6-ct120-homepage`: `latest_hash` står fortsatt på `d0c904a`, `deployed_hash` på `f84c1c5`. PullStack er kjørt, men årsaken til at hashen ikke oppdateres er **ikke undersøkt**.
- Neste steg: les Komodo-oppdateringsloggen for PullStack på `pc6-ct120-homepage`, rett årsaken, deploy, verifiser `deployed_hash == latest_hash` og at http://10.0.0.124:3009 viser pc7/pc8.
- Samme status er ført i nettverkskartet (Gitea/CT120) som «Planlagt v2.155».


## ⚠️ Nettverkskartet ligger IKKE i GitHub

**Nettverkskartet (`docs/network-map/`) redigeres og publiseres kun via Gitea på CT120.**

- Kilde: `CT120:/opt/moved-services/nettkart-repo/docs/network-map/nettverkskart.html` (origin = Gitea `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git`, CT118).
- Publisering: kjør `/usr/local/sbin/nettkart-publish` på CT120 etter commit. Skriptet pusher til Gitea, validerer versjon + endringsnotat og publiserer atomisk.
- Gjeldende regler: `PUBLISHING.md` i Gitea-kopien (samme mappe på CT120).
- `docs/network-map/` **finnes ikke i GitHub** (fjernet 10. nov 2026). Ikke opprett mappen igjen og ikke legg kart-HTML i GitHub — drift-vakten slår **kritisk** alarm hvis den dukker opp. Levende webrot er `CT120:/srv/nettkart/www`, utenfor alle Git-kopier; bare `nettkart-publish` (og kartets egne tjenester på CT120) skriver dit. Komodo-stacken `pc6-ct120-web` leverer bare nginx.
- Alt annet (Komodo-stacker, Homepage, Dashy, Ansible, kode, øvrig dokumentasjon) ligger i **GitHub**.
