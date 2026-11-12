# Samarbeidsflyt for flere AI-agenter

Reglene står i [AGENTS.md](../AGENTS.md), «START HER». Denne filen er bare en peker.

- GitHub (`Kingpro500/homelab-komodo`): `homelab-pr "tittel"` i klonen. Den rebaser på siste `main`, så flere agenter kan levere samtidig. Ved konflikt stopper den uten å pushe; løs konflikten og kjør den på nytt.
- Nettverkskartet (Gitea `Kingpro500/nettverkskart`): `nettkart-publish` på CT120. Samtidige økter slås sammen av `nettkart-merge`.
- Komodo deployer bare fra merget `origin/main`. `homelab-pr` gjør det og leser tilbake `deployed_hash`.
