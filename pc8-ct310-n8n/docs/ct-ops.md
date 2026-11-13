# CT-ops – kontrollert CT-endring med kvalitetssjekk

Navneendring av CT og Komodo-statuslinjen i nettverkskartet gjøres **ikke for hånd av en agent**.
De går gjennom n8n-webhooken `/ct-ops`, som kaller skriptet `ct-ops` på pc6 og deretter selv leser
Proxmox og det publiserte kartet på nytt. Svaret sier `ok: true` bare når alt er lest tilbake uten avvik.

Bakgrunn: 13. nov 2026 endret en agent Proxmox-navn og kart, sa «ferdig», og hoppet over Komodo og GitHub.
Reglene fantes; det som manglet var en vei som ikke lar seg gjøre halvveis.

## Bruk

`POST http://10.0.0.119:5678/webhook/ct-ops` med JSON. Ta med `"av": "<agent>"`.

| Handling | Body | Endrer noe? |
| --- | --- | --- |
| Revisjon av alle CT-er | `{"action":"audit"}` | nei |
| Fasit for én CT | `{"action":"verify","vmid":128}` | nei |
| Kartstatus, kontroll | `{"action":"map-check","vmids":[240,250]}` eller `"vmids":"all"` | nei |
| Kartstatus, rett og publiser | `{"action":"map-fix","vmids":[240]}` | kartet |
| Navneendring, plan | `{"action":"plan-rename","vmid":128,"service":"tom"}` | nei |
| Navneendring, utfør | `{"action":"apply","plan_id":"p128-…"}` | Proxmox, Komodo, GitHub, kart |

Valg på `plan-rename`: `"start_stop": true` (stoppet CT startes, endres og stoppes igjen) og
`"running_stacks": true` (kjørende stacker får også nytt navn og ny mappe).

### Navneendring: plan → godkjenning → utfør

1. `plan-rename` gir stegene, eventuelle blokkeringer og en `plan_id` (gyldig i 30 min). Roger får push.
2. Agenten viser stegene til Roger og **venter på et tydelig ja**.
3. `apply` med `plan_id`. Tilstanden kontrolleres på nytt; er noe endret siden planen, avvises den.
4. Svaret har `status`: `FERDIG`, `UFULLSTENDIG` (noe gjenstår – står i `remaining_deviations`),
   `FEILET` eller `BLOKKERT`. Bare `FERDIG` med `ok: true` kan rapporteres som ferdig.

## Hva ct-ops gjør og ikke gjør

- Navn er `<node>-ct<vmid>-<tjeneste>`. Komodo-serveren finnes via `connect_as` i gjestens Periphery
  (systemd eller container), ikke via navnelikhet.
- Servernavn byttes i Komodo sammen med `connect_as` i gjesten og restart av Periphery. Blir ikke
  serveren `Ok`, rulles begge deler tilbake.
- Stack: `project_name` låses først, mappen flyttes med `homelab-pr`, så byttes navn og `run_directory`.
  Stacker med relative stier i compose, delt mappe eller annen kilde enn dette repoet røres ikke;
  de listes under `not_handled`.
- Sperret: CT110 (Komodo Core), CT200/CT203 (Emby), CT310 (n8n). Rød drift-vakt stopper alle endringer.
- Sletter aldri noe, og oppretter aldri ny Komodo-server eller stack.
- Overskriften på CT-kortet i kartet endres ikke automatisk; det står som manuell oppfølging i svaret.

## Kartfarger (statuslinjen `.ct-method`)

| Farge | Betyr |
| --- | --- |
| Grønn | Periphery, Docker og Komodo-server er kontrollert Ok, og `verify` finner ingen avvik |
| Gul | Stoppet CT, eller kjørende CT med avvik eller noe som ikke er avklart |
| Rød | Bekreftet feil: server ikke Ok, Docker svarer ikke, eller Periphery melder seg med ukjent navn |

## Unntak

Et avvik som er bevisst godtas i `scripts/ct-ops-unntak.json` (CT-nummer, type, hva det gjelder, grunn).
Da teller det ikke, og CT-en kan bli grønn. Filen endres kun via `homelab-pr` etter Rogers ja.

## Nattlig kjøring

Kl. 04:40 kjøres full revisjon, og statuslinjer i kartet rettes der målt status har endret seg.
Roger varsles bare når bildet er endret siden forrige natt.

## Deler og gjenoppretting

| Del | Sted |
| --- | --- |
| Skript | `scripts/ct-ops` → `/usr/local/sbin/ct-ops` på pc6 |
| Tvungen SSH-kommando | `scripts/ct-ops-n8n` → `/usr/local/sbin/ct-ops-n8n` på pc6 |
| SSH-inngang | linje i `/root/.ssh/authorized_keys` på pc6: `restrict,from="10.0.0.119",command="/usr/local/sbin/ct-ops-n8n"` |
| n8n-credential | «pc6 ct-ops (tvungen kommando)» (SSH-nøkkel; privatnøkkelen finnes bare i n8n) |
| Arbeidsflyt | `workflows/ct-ops.json` (ingen hemmeligheter; credentials knyttes på ved import) |
| Logg | `/var/log/ct-ops.log` på pc6 |

Ved gjenoppretting: lag ny nøkkel, legg den offentlige delen i `authorized_keys` med opsjonene over,
opprett credentialen i n8n, importer arbeidsflyten og aktiver den.

`ct-ops` erstatter det halvferdige utkastet «CT reconcile orchestrator» for navneendring og kartstatus.
