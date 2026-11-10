# Drift-vakt — committet ≠ publisert

**Problemet den løser:** arbeid blir merget i GitHub eller committet i kartkilden,
men aldri deployet eller publisert. Neste agent legger så nye commits oppå, og
etter en stund vet ingen hva som faktisk kjører.

**Prinsipp:** ingenting stopper opp. Avvik gir en **stor advarsel** øverst i
nettverkskartet og en push til telefonen. **Neste arbeidsrunde starter med å rydde
opp i advarselen**, ikke med nytt arbeid oppå.

## Hvor du ser status

| Hvor | Hva |
| --- | --- |
| Øverst i nettverkskartet (http://10.0.0.124:3020/) | Rød boks = kritisk, gul = advarsel, grønn linje = alt i orden |
| `GET http://10.0.0.135:9118/drift` | Full JSON (ingen auth, ingen hemmeligheter) |
| Telefon via n8n `homelab-alerts` | Push ved **nye** kritiske funn, én påminnelse per dag fra kl. 09 og `[LØST]` når alt er ryddet. Aldri mellom 23 og 06 |

## Hva som sjekkes

| Nivå | Sjekk |
| --- | --- |
| **Kritisk** | Komodo-stack: filer i stackens mappe er endret i `main` etter `deployed_hash` (merget, men ikke deployet) |
| **Kritisk** | Kartkilden på CT120 (`/opt/moved-services/nettkart-repo`): ucommittede endringer, commits som ikke er pushet/publisert, gren ≠ `main`, eller live-kartet ≠ siste commit |
| **Kritisk** | GitHub- eller Komodo-API svarer ikke fra Hermes |
| **Kritisk** | `docs/network-map/` finnes i GitHub (kartet skal kun ligge i Gitea), eller nginx på CT120 monterer ikke `/srv/nettkart/www` |
| Advarsel | Åpen PR eldre enn 24 t |
| Advarsel | Gren med commits som ikke er i `main`, uten PR, eldre enn 3 døgn |
| Advarsel | Lokale kloner (Hermes `~/homelab-komodo`) som er skitne, står på feil gren eller er bak/foran `main` |
| Advarsel | Komodo `remote_errors` på en stack |
| Kjent (grå) | Bevisst pausede stacker (`KNOWN` i skriptet) og ferdige/forlatte grener som kan ryddes |

## Rutine når advarselen er rød eller gul

1. **Ikke start nytt arbeid og ikke lag nye commits eller PR-er oppå.** Les listen.
2. Ta punktene ovenfra (kritisk først). For hvert punkt står det et tiltak (→).
   - *Merget, men ikke deployet:* Komodo `PullStack` + `DeployStack`, verifiser `deployed_hash == latest_hash`.
   - *Kartkilden ucommittet/ikke publisert:* commit og kjør `/usr/local/sbin/nettkart-publish` på CT120.
   - *Åpen PR / gren uten PR:* fullfør den (merge + deploy) eller lukk den. Spør Roger hvis det er uklart.
   - *Skitten klone:* få det som skal beholdes inn via PR, og sett klonen tilbake til `main`.
3. **Aldri slett** grener, stacker, CT-er eller data for å få varselet grønt. Spør Roger.
4. Er avviket bevisst (f.eks. pause), legg det i `KNOWN` i `homelab_drift_check.py` med en forklaring, i én PR.
5. Kjør vakten på nytt og sjekk at kartet viser grønt eller bare grått:
   `pct exec 130 -- su - hermes -c 'python3 ~/.hermes/scripts/homelab_drift_check.py --no-notify'` (på pc7).

## Installasjon (filene i denne mappen er kilden)

Hermes, CT130 på **pc7** (`10.0.0.107`):

| Fil i repoet | Installeres som |
| --- | --- |
| `homelab_drift_check.py` | `/home/hermes/.hermes/scripts/homelab_drift_check.py` (eier `hermes`) |
| `homelab-drift.service`, `homelab-drift.timer` | `/etc/systemd/system/`, deretter `systemctl enable --now homelab-drift.timer` |

`GET /drift` serveres av `homelab_audit_server.py` (port 9118) fra `~/.hermes/state/drift.json`.

CT120 på **pc6**:

| Fil i repoet | Installeres som |
| --- | --- |
| `ct120-nettkart-drift.py` | `/usr/local/sbin/nettkart-drift` (0755) |
| `nettkart-drift.cron` | `/etc/cron.d/nettkart-drift` |

Den skriver `nettkart-drift.json` i webroten `/srv/nettkart/www`. Hermes leser filen via
`http://10.0.0.124:3020/nettkart-drift.json`.

Banneret i kartet (`#drift-banner`) ligger i Gitea-kilden, jf. `PUBLISHING.md`, regel 11.
