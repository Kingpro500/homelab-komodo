# Hermes tilgangsmatrise (verifisert live 2026-11-10)

Test kjørt av Hermes (bruker `hermes` på hermes-verten, uid 1000). Kun variabelNAVN fra `.env` er lest, aldri verdier. Oppdater datoen når du re-verifiserer.

## Lokalt (hermes-verten)
- Bruker `hermes`, **ingen sudo** (`sudo: command not found`). Verktøy: git, python3, node, curl, jq. Ikke docker, gh.
- Lokal dockctl/audit-tjeneste lytter på :9118 (python3). `/health` med `AUDIT_TOKEN` -> `{"ok":true,"service":"homelab-audit"}`.

## SSH (nøkkel `~/.ssh/id_ed25519_hermes`, MÅ angis med `-i ... -o IdentitiesOnly=yes`)
| Node | IP | root | hermes | sudo |
|---|---|---|---|---|
| pc8 | 10.0.0.102 | OK | OK | ingen sudo installert |
| pc9 | 10.0.0.103 | OK | OK | hermes: NOPASSWD kun /usr/sbin/pct; root ALL |
| pc1 | 10.0.0.112 | OK | - | root |
| pc6 | 10.0.0.120 | OK | - | root |
| pc7 | 10.0.0.107 | OK | - | root |
- Alle 5 noder i samme cluster (pve 9.2). `ct-new`, `ct-komodo`, `ct-periphery-*` ligger i /usr/local/sbin på pc8 og pc9.
- Vanlig `ssh hermes@ip` uten `-i` feiler (ingen standardnøkkel, ingen ~/.ssh/config). Det er ikke et reelt tilgangsproblem.
- Sporadisk "Connection reset" på port 22 ved mange raske forbindelser (rate-limit). Vent og prøv igjen.
- Andre nøkler i ~/.ssh: `ct130_komodo`, `komodo_core_temp`, `media_recovery`, `netalertx_leases`. Testet mot Unraid(.101), pc8, pc9, OPNsense(.1), Komodo(.117), n8n(.119), HA(.7) som root og hermes: **ingen treff**. Mål ukjent (sannsynligvis enkelt-CT-er).

## API-er (variabelnavn i ~/.hermes/.env -> HTTP-status, live)
| Tjeneste | Variabler | Resultat |
|---|---|---|
| Proxmox | PROXMOX_URL/TOKEN_ID/TOKEN_SECRET (10.0.0.102:8006) | 200, ser alle 5 noder. Token er PVEAdmin, ikke root@pam (kan ikke sette keyctl=1; bruk SSH root) |
| Emby (CT200 pc6, 10.0.0.150:8096) | EMBY_API_KEY | 200. Standby: CT203 på pc9 |
| Home Assistant 10.0.0.7:8123 | HASS_URL/HASS_TOKEN | 200 |
| n8n 10.0.0.119:5678 | N8N_URL/N8N_API_KEY | 200 |
| OPNsense 10.0.0.1 | OPNSENSE_URL/API_KEY/API_SECRET | 200 (basic auth; leseendepunkter krever POST+JSON) |
| Unraid 10.0.0.101 | UNRAID_URL/UNRAID_API_KEY | 200 (GraphQL, x-api-key) |
| Komodo 10.0.0.117:9120 | KOMODO_ADDRESS/API_KEY/API_SECRET | 200 (POST /read, X-Api-Key + X-Api-Secret) |
| GitHub | GITHUB_TOKEN | 200. Scopes: repo, workflow, delete_repo, admin:org, admin:repo_hook, admin:public_key, admin:gpg_key, admin:enterprise, delete:packages, write:packages, codespace, gist, project, audit_log. Bred, bruk med omhu. `Kingpro500/homelab-komodo` lesbar |
| OpenRouter | OPENROUTER_API_KEY | 200 |
| OpenAI | OPENAI_API_KEY | 200 |
| dockctl/audit :9118 | CONTROL_TOKEN_DOCKCTL, AUDIT_TOKEN | audit-health 200. Kontroll-token ikke brukt |
| LM-server 10.0.0.133:11434 | LM_BASE_URL/LM_API_KEY | **Nede/ikke nåbar (timeout)** |
| Browserbase | BROWSERBASE_* (kun innstillinger) | Ingen API-nøkkel i .env. Ikke brukbar |
| OPENCODE_GO_API_KEY | | Ikke testet |

## Mangler / begrensninger
- Ingen sudo lokalt. Root er kun via SSH til Proxmox-nodene.
- API-token kan ikke opptre som root@pam.
- Ingen SSH-tilgang bevist til Unraid, OPNsense, Komodo-host, n8n, HA (kun API). CT-er nås via `pct exec` fra node-root.
- LM-server (10.0.0.133) svarer ikke.
- Browserbase mangler nøkkel; ingen GUI/nettleserstyring utenom desktop-preview.
- Hemmeligheter som ikke ligger i .env. Subagenter kan ikke spørre brukeren.

## Gitea / nettverkskart (verifisert live 2026-11-11)
- Gitea 10.0.0.176:3000 (CT118 pc6, running): web 200, repo krever innlogging (anonym 404, `git ls-remote` uten creds feiler). Hermes har INGEN Gitea-variabler i `.env`; tilgang går via pc6-ct120-monitoring (`/etc/nettkart/git-credentials`, `gitea-sync.token`), kun root på pc6.
- pc6-ct120-monitoring (CT120 på pc6, 10.0.0.120; kartets arbeidskopi + nettkart-publish): `/opt/moved-services/nettkart-repo` ren, i synk med origin/main (v2.214), `git fetch` OK. `/usr/local/sbin/nettkart-publish` finnes og er kjørbar. Ikke kjørt (ville publisert); ingen dry-run-flagg.
- Live 10.0.0.124:3020 viser v2.214 (lik repo), PUBLISHING.md 200.
- Regler: se skill `nettverkskart-vedlikehold`, live PUBLISHING.md, GitHub AGENTS.md/docs/ACCESS-RUNBOOK.md. Kun kart + daily-report i Gitea, alt annet i GitHub.

## Sånn re-verifiserer du
SSH: `ssh -i ~/.ssh/id_ed25519_hermes -o IdentitiesOnly=yes -o BatchMode=yes root@<ip> id -un`. API: `set -a; . ~/.hermes/.env; set +a` og curl mot URL-ene over; skriv aldri ut verdier.
