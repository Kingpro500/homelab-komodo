# Contributions and multi-agent integration

## ⚠️ Nettverkskartet ligger IKKE i GitHub

**Nettverkskartet (`docs/network-map/`) redigeres og publiseres kun via Gitea på CT120 (`pc6-ct120-monitoring`).**

- Kilde: `CT120:/opt/moved-services/nettkart-repo/docs/network-map/nettverkskart.html` (origin = Gitea `http://10.0.0.176:3000/Kingpro500/homelab-komodo.git`, CT118).
- Publisering: kjør `/usr/local/sbin/nettkart-publish` på CT120 etter commit. Skriptet pusher til Gitea, validerer versjon + endringsnotat og publiserer atomisk.
- Gjeldende regler: `PUBLISHING.md` i Gitea-kopien (samme mappe på CT120).
- `docs/network-map/` **finnes ikke i GitHub** (fjernet 10. nov 2026). Ikke opprett mappen igjen og ikke legg kart-HTML i GitHub — drift-vakten slår **kritisk** alarm hvis den dukker opp. Levende webrot er `CT120:/srv/nettkart/www`, utenfor alle Git-kopier; bare `nettkart-publish` (og kartets egne tjenester på CT120) skriver dit. Komodo-stacken `pc6-ct120-web` leverer bare nginx.
- Alt annet (Komodo-stacker, Homepage, Dashy, Ansible, kode, øvrig dokumentasjon) ligger i **GitHub**.



## Standard

Work from a dedicated branch. Do not push directly to `main` when other agents may be active.

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/<agent>/<task>
```

Use a separate `git worktree` for each concurrent agent. Keep commits focused and do not include unrelated generated files.

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
