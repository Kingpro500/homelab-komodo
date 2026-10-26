# Samarbeidsflyt for flere AI-agenter

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
