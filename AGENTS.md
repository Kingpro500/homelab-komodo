# Instruksjoner for AI-agenter (Codex, Claude, Hermes)

> 🔑 **Hva har agentene tilgang til?** Verifisert tilgangsmatrise: [`docs/hermes-access.md`](docs/hermes-access.md) (Hermes-sesjoner: skillen `hermes-access-matrix`). Fremgangsmåte og ruter: [`docs/ACCESS-RUNBOOK.md`](docs/ACCESS-RUNBOOK.md).
> **Vedlikeholdsplikt:** endrer du en tilgang, vert, nøkkel eller credential-plassering, oppdater `docs/ACCESS-RUNBOOK.md` og `docs/hermes-access.md` i samme PR.

## ⛔ Flytting av CT: aldri flytt bare gjesten

Før enhver Proxmox-flytting, omdøping eller gjenbruk skal agenten følge den komplette kontrollen i [`docs/proxmox-komodo-github-migration-runbook.md`](docs/proxmox-komodo-github-migration-runbook.md). En flytting er ikke ferdig før Proxmox, gjestens Periphery, Komodo-server, `GetStack.config.server_id`, GitHub-kilde/run directory og tjenestehelse er verifisert samlet. `ListStacks` alene er ikke nok; hent `GetStack` for hver berørt stack. Ved avvik: stopp mutasjoner, merk nettverkskartet umiddelbart, og ikke opprett duplikatserver eller ny stack som snarvei.

## 🆕 Ny CT: bruk en tom CT Roger har laget, ikke `ct-new` selv

Agenter oppretter **ikke** nye CT-er på egen hånd. Rekkefølge:

1. **Gjenbruk** en ledig, tom CT som allerede er registrert i Komodo (sjekk `ListServers` mot Proxmox og kartet; en CT med innhold, `test`-CT eller arkiv-CT er ikke «tom» før Roger har bekreftet det).
2. Finnes ingen: **be Roger opprette en tom CT** (`ct-new <tjeneste> [ram] [disk] [kjerner]` på noden, som registrerer den i Komodo), og vent til serveren er `Ok` i Komodo.
3. Ta så over CT-en: endre størrelse (`pct set`/`pct resize`), lag stack-mappen `<node>-ct<id>-<tjeneste>/` via PR, opprett stacken på den eksisterende Komodo-serveren (`CreateStack` → `PullStack` → `DeployStack`). Ikke kjør `ct-komodo` på nytt for å gi CT-en nytt navn; det lager en ekstra Komodo-server.
4. Roger vil ha siste versjon: «oppdater» betyr oppgrader til nyeste (ikke pinn). `DeployStack` kjører `compose pull`, så `:latest` gir nyeste. Ta config-backup først og verifiser helse etterpå.
5. Oppdater Homepage og nettverkskartet i samme runde.

## 🔌 Har en CT Komodo Periphery? Sjekk riktig sted

Standarden for **nye CT-er** er **Periphery som Docker-container** (`ct-new` → `ct-komodo` → `komodo-bootstrap`, mal: `templates/lxc-komodo-v2/periphery-compose.yml`). Filer ligger i `/opt/komodo/periphery/`, Komodo-root er `/opt/komodo`. Eldre CT-er (migrert til systemd 10. nov) har systemd-Periphery med alt i `/etc/komodo`; de er IKKE feil, men skal over til container-standarden (se README). Sjekk begge:

```sh
pct exec <ctid> -- docker ps --filter name=komodo-periphery   # ny standard
pct exec <ctid> -- systemctl is-active periphery              # gammel (systemd)
# og i Komodo: serveren <node>-ct<id>-<navn> har state Ok
```

**Felles regel:** Nye CT-er bruker Docker-Periphery i `/opt/komodo/periphery/`. Eksisterende systemd-Periphery i eldre CT-er er ikke en feil; migrering til container-standarden gjøres senere, kontrollert og uten å avbryte tjenester. Komodo skal ha **én** server per CT med navn `<node>-ct<id>-<navn>` og status `Ok` når CT-en er tilgjengelig. Sjekk Proxmox, gjestens Periphery og Komodo-registeret mot hverandre før du registrerer noe på nytt; et gammelt registertreff eller `Ok` alene beviser ikke at agenten er riktig eller at CT-en kjører. Duplikater skal undersøkes og ryddes kontrollert, ikke opprettes. En stoppet eller utilgjengelig CT merkes «ikke verifisert», ikke som bekreftet feil. Unntak: CT110 (Core) har Periphery i Core sin Compose.

## 🚨 Start HVER økt med disse to sjekkene

### ⛔ Kan du ikke publisere, merge eller deploye? Si det tydelig, og meld det

Gjelder alle agenter og alle steder: GitHub (PR/merge), Komodo (deploy), Gitea/nettverkskartet (`nettkart-publish`) og alt annet som skal ut i drift.

1. **Prøv de dokumenterte rutene først** (se Tilgang under og `docs/ACCESS-RUNBOOK.md`). En feilende `gh`/`GH_TOKEN` i din egen sandkasse betyr ikke at tilgangen mangler.
2. **Når det likevel ikke går, skal svaret til Roger begynne med** `⛔ KAN IKKE PUBLISERE:` etterfulgt av hva det gjelder, hvilken rute du prøvde, og den nøyaktige feilmeldingen. Ikke gjem det nederst i svaret.
3. **Meld det i drift-vakten med en gang**, fra pc6 (homelab-ssh) eller CT120 (`pc6-ct120-monitoring`):
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


## ⚠️ Gitea eller GitHub: lokale sider i Gitea, alt annet i GitHub

**Gitea inneholder kun de lokale sidene: nettverkskartet og advarselsiden. Alt annet ligger i GitHub.**

| Hva | Fil (i Gitea) | Kilde |
| --- | --- | --- |
| Nettverkskart | `docs/network-map/nettverkskart.html` | **Gitea** |
| Advarselsiden (daglig helserapport) | `docs/network-map/daily-report.html` | **Gitea** |
| Alt annet: Komodo-stacker, Homepage, Dashy, Ansible, n8n, scripts, drift-vakt, spill (f.eks. Oslo Børs), dokumentasjon | | **GitHub** |

- Gitea: `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git` (CT118). Arbeidskopi: `CT120:/opt/moved-services/nettkart-repo`.
- Publisering: commit, så `/usr/local/sbin/nettkart-publish` på CT120. Krever at CT118 og CT120 kjører.
- Gjeldende regler: `README.md`/`AGENTS.md` og `docs/network-map/PUBLISHING.md` i Gitea-kopien.
- Legg aldri annet enn lokale sider i Gitea, og legg aldri kartet eller advarselsiden i GitHub.
