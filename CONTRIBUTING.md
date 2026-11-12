# Contributions

Reglene står i [AGENTS.md](AGENTS.md), «START HER». Kort:

- Alt i dette repoet leveres med `homelab-pr "tittel"`. Den lager gren og PR, merger, sletter grenen og deployer. Ikke push, lag grener eller PR-er for hånd.
- Nettverkskartet ligger ikke her, men i Gitea `Kingpro500/nettverkskart` (`nettkart-publish` på CT120).
- Endrer du en tilgang, vert, nøkkel eller credential-plassering: oppdater `docs/ACCESS-RUNBOOK.md` og `docs/hermes-access.md` i samme leveranse.
- Kjør `git diff --check`, `bash -n` på skript og valider YAML/Compose før du leverer.
- Aldri commit secrets, tokens, passord, private nøkler eller connection strings.
