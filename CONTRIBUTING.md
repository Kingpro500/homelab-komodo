# Contributions and multi-agent integration

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
