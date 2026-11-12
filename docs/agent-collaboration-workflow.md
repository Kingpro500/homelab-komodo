# Samarbeidsflyt for flere AI-agenter

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

## Mål

`main` er integrasjons- og deploy-branch. Agenter skal ikke pushe direkte til `main` når flere arbeidsprosesser kan skrive samtidig.

## Branch-regel

Hver oppgave bruker en egen branch:

```text
agent/<agentnavn>/<kort-oppgave>
```

Eksempler:

```text
agent/hermes/fix-komodo-topology
agent/codex/update-network-map
agent/claude/compose-validation
```

## Før arbeid

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/<agentnavn>/<kort-oppgave>
```

Bruk en separat `git worktree` når flere agenter kjører på samme maskin samtidig. Ikke del samme arbeidskatalog mellom agenter.

## Under arbeid

- Endre bare filer som hører til oppgaven.
- Ikke bruk `reset --hard`, `clean`, force-push eller sletting av andres branches uten eksplisitt godkjenning.
- Kjør relevante valideringer før commit.
- Commit én logisk oppgave om gangen.
- Ikke legg secrets, tokens eller connection strings i Git.

## Før push

```bash
git diff --check
git fetch origin main
git rebase origin/main
git push -u origin HEAD
```

Hvis rebase får konflikt: stopp, inspiser konflikten og løs den eksplisitt. Ikke overskriv andre agenters endringer automatisk.

## Integrasjon

Pull request er normal vei inn i `main`. Integratoren skal kontrollere:

- at branch er rebaset mot siste `main`
- YAML-/Compose-syntaks og relevante tester
- at ingen secrets er commitet
- Homepage og nettverkskart ved nye tjenester eller plasseringer
- prosjekt-README og runbook ved operasjonelle endringer
- at deploy skjer fra den merged committen på `origin/main`

## Deployregel

Komodo skal deploye fra den verifiserte `origin/main`-commiten, ikke fra en agents lokale arbeidsbranch. Etter merge skal `latest_hash`, `deployed_hash` og `remote_errors` leses tilbake.

## Konkret situasjon med parallell push

Hvis push avvises med `fetch first`:

```bash
git fetch origin main
git rebase origin/main
git push origin HEAD:main
```

Dette er en reparasjonsprosedyre, ikke normal arbeidsflyt. Branch + PR forebygger at agenter konkurrerer direkte om `main`.
