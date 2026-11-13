# Instruksjoner for AI-agenter (Codex, Claude, Hermes)

## ▶️ START HER — reglene som alltid gjelder

Dette er den ene kilden. `CLAUDE.md`, `CONTRIBUTING.md` og `docs/agent-collaboration-workflow.md` peker hit. Står det noe annet et annet sted, gjelder dette.

1. **To steder, aldri bland dem.** Nettverkskartet og advarselsiden → **Gitea** `Kingpro500/nettverkskart`. Alt annet (kode, stacker, drift-vakt, n8n, skript, dokumentasjon) → **GitHub** `Kingpro500/homelab-komodo`. Navnet `homelab-komodo` betyr alltid GitHub.
2. **GitHub: bare `homelab-pr "tittel"`.** Gjør endringen i klonen (CT130 `~/homelab-komodo`, pc6 `/root/claude-work/homelab-komodo`) og kjør kommandoen. Den lager gren og PR, squash-merger, sletter grenen, setter klonen på `main` og deployer berørte Komodo-stacker. Aldri rå `git push`, `gh pr`, egne grener eller worktrees. Aldri be Roger merge.
3. **Kartet: bare `nettkart-publish`.** Rediger kartet i `CT120:/opt/moved-services/nettkart-repo` og kjør `nettkart-publish "hva er endret" --av <agent>`. Den setter versjonsnummer, endringsnotat og logglinje og committer selv; ikke før dem for hånd. Ingen grener og ingen PR; Gitea avviser dem. Regler: `docs/network-map/PUBLISHING.md` i Gitea.
4. **Berører oppgaven begge steder,** er det to leveranser: én med `homelab-pr` og én med `nettkart-publish`.
5. **Ferdig er det først når verktøyet sier det** (`✅ FERDIG` / `Published`). Skriver `homelab-pr` «IKKE deployet», eller feiler noe: begynn svaret til Roger med `⛔ KAN IKKE PUBLISERE:` og meld det med `homelab-blokkert` (se under).
6. **Drift-vakten** (`http://10.0.0.135:9118/drift`, øverst i kartet): **rød = stopp** og spør Roger om hvert røde funn før du gjør noe mer. **Gul stopper ikke**; rydd når det er trygt. Lagring er gul fra 80 % og rød fra 99 %; tersklene står i `docs/network-map/drift-regler.json` i Gitea og endres der.
7. **Emby (CT200, pc6) går foran alt,** også rød stopp. Aldri restart, flytt eller oppgrader Emby uten stream-sjekk og uten at Roger vet det. Prioritet 2 er nettverksstabilitet.
8. **Ikke lag CT-er selv, og flytt aldri bare gjesten** (se avsnittene under).
9. **Homepage og Dashy er på pause.** Ikke rør, ikke nevn, ikke tilby.
10. **Rydd etter deg.** Ikke legg igjen engangsskript i `/root`, ekstra kloner eller midlertidige filer. Slett aldri andres grener, stacker, CT-er eller data uten å spørre Roger.

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

## 🔗 Noen containere dør når du deployer naboen

`tunarr-nfs-health-session-checker` i CT106 har `network_mode: "container:tunarr"`.
Den låner nettverket til Tunarr-containeren, så i det Tunarr blir gjenopprettet
forsvinner navnerommet den satt i: containeren dør med exit 137, og `docker start`
nekter med «joining network namespace of container: No such container».

**Deployer du `pc9-ct106-tunarr`, må du deploye `pc9-ct106-nfs-health` etterpå.**
Da bygges session-checkeren på nytt mot den nye Tunarr-containeren. Sett dette i
sammenheng hvis en nabocontainer plutselig står som Exited (137) uten logg.

Let etter `network_mode: "container:` eller `service:` før du deployer noe —
samme felle gjelder alle slike par.


## 🧹 Avslåtte Docker-Peripheryer fra systemd-overgangen

Elleve CT-er har en stoppet `komodo-periphery`-container ved siden av den aktive
systemd-agenten, fra overgangen 10. nov 2026: CT101, CT120, CT200 og CT250 på pc6,
CT115 på pc7, CT310 på pc8, og CT103, CT106, CT111 og CT203 på pc9. Alle har
`restart=no`, så de starter ikke av seg selv.

De fleste er harmløse — `PERIPHERY_CONNECT_AS` er tom eller lik systemd-navnet.
**Unntaket er CT120**, der `.env` sier `pc6-ct104-media-downloaders`, et servernavn
som ikke finnes i Komodo. Startes den manuelt, får CT120 to agenter og det dukker
opp en falsk server. Ikke start noen av dem, og ikke slett dem uten å si det til
Roger først — de er den eneste veien tilbake hvis systemd-agenten svikter.

Uten Periphery i det hele tatt: CT130 (Hermes, trenger ingen), CT152, CT180 og
CT137. CT137 har heller ingen Komodo-server.


## 🔒 Navneendring og kartstatus går gjennom n8n `/ct-ops` — aldri for hånd

1. **Bytt aldri navn på en CT med `pct set --hostname`, i Komodo eller i repoet for hånd.** Bruk `POST http://10.0.0.119:5678/webhook/ct-ops`: først `plan-rename`, vis stegene til Roger, vent på et tydelig ja, så `apply`.
2. **Endre aldri Komodo-statuslinjen (`.ct-method`) i kartet for hånd.** Bruk `map-check` og `map-fix`.
3. **«Ferdig» betyr `ok: true` i svaret fra `/ct-ops`.** Lim inn `status` og `kvalitetssjekk` i svaret til Roger. Er `ok` false: gjengi status og avvik ordrett, og ikke prøv en annen vei.
4. Bevisste avvik godtas bare i `scripts/ct-ops-unntak.json`, via `homelab-pr`, etter Rogers ja.

Alt står i [pc8-ct310-n8n/docs/ct-ops.md](pc8-ct310-n8n/docs/ct-ops.md).

## 🏷️ Komodo-navn lyver — les beskrivelsen, ikke navnet

Mange servere og stacker i Komodo heter fortsatt det CT-nummeret de hadde før en flytting. `pc6-ct109-*` kjører i CT210, `pc8-ct102-core` er CT110, `pc9-ct124-uisp` står på pc7. **Hver slik oppføring har en beskrivelse som sier hvor den faktisk kjører (satt 12. nov 2026). Stol på beskrivelsen og Proxmox, aldri på navnet.**

**Ikke «rydd» navnene.** Et navnebytte i Komodo er ikke kosmetikk:

- **Server:** navnet er identiteten agenten melder seg på med (`PERIPHERY_CONNECT_AS` i `/opt/komodo/periphery/.env` i CT-en, for de som kobler ut). Bytter du navnet i Komodo uten å endre `.env` og restarte agenten, mister Komodo kontakten med CT-en og alle stackene der.
- **Stack:** når `project_name` er tomt, utledes Compose-prosjektet av stacknavnet. Et navnebytte gir nytt prosjekt, og de gamle containerne blir foreldreløse.
- **Sletting av en stack som kjører** kjører `compose down --remove-orphans` på CT-en. Bare stacker som står `down`/`unknown` kan slettes uten at noe stopper.

Skal et navn rettes, gjøres det for én CT om gangen sammen med Roger: sett `project_name` eksplisitt (stack) eller endre `.env` og restart agenten (server), og les tilbake at alt står `Ok` og at containerne kjører.

## 🔌 Har en CT Komodo Periphery? Sjekk riktig sted

Standarden for **nye CT-er** er **Periphery som Docker-container** (`ct-new` → `ct-komodo` → `komodo-bootstrap`, mal: `templates/lxc-komodo-v2/periphery-compose.yml`). Filer ligger i `/opt/komodo/periphery/`, Komodo-root er `/opt/komodo`. Eldre CT-er (migrert til systemd 10. nov) har systemd-Periphery med alt i `/etc/komodo`; de er IKKE feil, men skal over til container-standarden (se README). Sjekk begge:

```sh
pct exec <ctid> -- docker ps --filter name=komodo-periphery   # ny standard
pct exec <ctid> -- systemctl is-active periphery              # gammel (systemd)
# og i Komodo: serveren <node>-ct<id>-<navn> har state Ok
```

**Felles regel:** Nye CT-er bruker Docker-Periphery i `/opt/komodo/periphery/`. Eksisterende systemd-Periphery i eldre CT-er er ikke en feil; migrering til container-standarden gjøres senere, kontrollert og uten å avbryte tjenester. Komodo skal ha **én** server per CT med navn `<node>-ct<id>-<navn>` og status `Ok` når CT-en er tilgjengelig. Sjekk Proxmox, gjestens Periphery og Komodo-registeret mot hverandre før du registrerer noe på nytt; et gammelt registertreff eller `Ok` alene beviser ikke at agenten er riktig eller at CT-en kjører. Duplikater skal undersøkes og ryddes kontrollert, ikke opprettes. En stoppet eller utilgjengelig CT merkes «ikke verifisert», ikke som bekreftet feil. Unntak: CT110 (Core) har Periphery i Core sin Compose.

## 🚨 Utdyping: blokkert publisering, drift-vakt og GitHub-tilgang

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

- `level` er `kritisk` (rød): **stopp.** Ingen nye commits, PR-er eller infrastrukturendringer før Roger har sagt hva som skal gjøres med hvert røde funn. `advarsel` (gul) stopper ikke arbeidet; rydd når det er trygt. Rutine: [pc7-ct130-hermes/drift-vakt/README.md](pc7-ct130-hermes/drift-vakt/README.md).
- Kan du ikke rydde et funn, skriv det øverst i svaret til Roger.
- **GitHub: bruk alltid `homelab-pr "tittel"`** i klonen (CT130 `~/homelab-komodo`, pc6 `/root/claude-work/homelab-komodo`). Den lager gren og PR, merger, sletter grenen og deployer berørte Komodo-stacker i én kommando, og sier nøyaktig hva som ikke er deployet. Aldri rå `git push`, `gh pr` eller egne grener, og aldri be Roger merge.
- **Gitea heter `Kingpro500/nettverkskart`** (ikke `homelab-komodo`) og tar bare imot kartet på `main`; alt annet avvises av en sperre. Kartet publiseres med `nettkart-publish` på CT120.

### 2. GitHub-tilgang — den finnes. Si aldri «mistet tilgang» før du har prøvd rutene under

Din egen sandkasse (Codex cloud, Claude Cowork o.l.) kan mangle `gh`-login eller ha et ugyldig `GH_TOKEN`. **Det betyr ikke at homelab-ets GitHub-tilgang er borte.** Bruk de faste rutene:

| Behov | Fast rute | Sjekk (kun lesing) |
| --- | --- | --- |
| git lese/push | SSH til pc6 (`10.0.0.120`), klonen `/root/claude-work/homelab-komodo` med deploy-nøkkel `/root/.ssh/claude_github_deploy` (satt i `core.sshCommand`) | `cd /root/claude-work/homelab-komodo && git fetch origin && git log -1 --oneline origin/main` |
| PR/merge (API) | Hermes CT130 på **pc7** (`10.0.0.107`), `GITHUB_TOKEN` i `/home/hermes/.hermes/.env`. Fra pc6: `ssh root@10.0.0.107 'pct exec 130 -- …'` | `GET https://api.github.com/repos/Kingpro500/homelab-komodo` med tokenet → 200 |
| PR/merge (reserve) | Fine-grained token på pc8: `/root/.config/claude/github.env` | samme |
| Codex | `git@github.com:Kingpro500/homelab-komodo.git` med Codex sin egen SSH-identitet (se ACCESS-RUNBOOK) | `git ls-remote origin HEAD` |

Drift-vakten tester GitHub-API-et hvert 15. minutt. `github_access.ok: true` i `/drift` betyr at tilgangen virker, og at feilen ligger i din egen sandkasse. Rapporter **ruten som feilet og den nøyaktige feilmeldingen**, aldri bare «ingen tilgang». Aldri vis, kopier eller committ tokenverdier. Mer: [docs/ACCESS-RUNBOOK.md](docs/ACCESS-RUNBOOK.md).

Før arbeid i en klone: `git switch main && git pull --ff-only`. `homelab-pr` henter selv tilgangen fra rutene over.


## ⏸️ Status: Homepage- og Dashy-arbeid på PAUSE (8. nov 2026)

Brukeren har bevisst satt Homepage- og Dashy-arbeidet på pause. Ikke redeploy Homepage eller Dashy før brukeren tar opp saken igjen.
- Dashy: kjører ikke. Containeren ligger stoppet i CT392 og tjenesten står under compose-profilen `pause` i `pc6-ct392-dashboards/docker-compose.yml`, så verken `compose up` eller Komodos Deploy starter den. Referansekonfigurasjonen med endringen fra #78 (ny flis pc7, pc8 som OPNsense-reserve) ligger i `pc6-ct392-dashboards/dashy-config/conf.yml`. Kartet: «Planlagt v2.156». Den gamle stacken `pc6-ct109-dashy` er slettet 12. nov 2026 (den pekte på CT210, der Dashy ikke har ligget siden 11. nov).

- Merget i GitHub, men **ikke deployet**: PR #78 (`13d44c2`) – pve→pc8, ny pc7-flis, Home Assistant på pc9, Netdata pc8, Pi-hole CT101 pc6, OPNsense VM191 (pc7) / VM190 (pc8). Gjelder `homepage/config/services.yaml`, `homepage/services.runtime.yaml`, `pc6-ct392-dashboards/dashy-config/conf.yml` (het før `pc6-ct109-dashy/config/conf.yml`).
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

- Gitea: `http://10.0.0.176:3000/Kingpro500/nettverkskart.git` (CT118). Arbeidskopi: `CT120:/opt/moved-services/nettkart-repo`.
- Publisering: commit, så `/usr/local/sbin/nettkart-publish` på CT120. Krever at CT118 og CT120 kjører.
- Gjeldende regler: `README.md`/`AGENTS.md` og `docs/network-map/PUBLISHING.md` i Gitea-kopien.
- Legg aldri annet enn lokale sider i Gitea, og legg aldri kartet eller advarselsiden i GitHub.
