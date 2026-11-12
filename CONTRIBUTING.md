# Contributions and multi-agent integration

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

## Standard

Work from a dedicated branch. Do not push directly to `main` when other agents may be active.

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/<agent>/<task>
```

Use a separate `git worktree` for each concurrent agent. Keep commits focused and do not include unrelated generated files.

## Access documentation must stay current

Changing an access path, host, SSH key or credential location requires updating `docs/ACCESS-RUNBOOK.md` and `docs/hermes-access.md` in the same PR. See [AGENTS.md](AGENTS.md).

## Required checks

Before opening a PR or handing work to the integrator:

```bash
git diff --check
```

Also run the validators relevant to the changed files:

- YAML: parse with the repository's available YAML tooling.
- Shell: `bash -n <script>`.
- Compose: validate with the target Compose implementation where available.
- Documentation: check links and ensure inventory, Homepage, and network-map entries agree.

Never commit secrets, tokens, passwords, private keys, or connection strings.

## Integration policy

`main` is the only branch used for verified deployment. The integrator must fetch the latest `main`, rebase or merge the PR through the normal GitHub review path, and deploy only the resulting merged commit.

If a direct push is rejected because `main` moved, do not force-push. Fetch, rebase the isolated branch, rerun checks, and retry. Stop on conflicts rather than choosing one side automatically.
