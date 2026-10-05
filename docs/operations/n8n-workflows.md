# Drift av n8n-arbeidsflyter — prinsipper

Slik bygges, sikres, versjoneres og gjenopprettes n8n-arbeidsflytene i denne
homelab. Gjelder begge de aktive workflowene i `pc6-ct103-n8n`.

## Hvor ting bor

```
n8n (kjørende, 10.0.0.119:5678)   ← sannheten om HVA som kjører akkurat nå
GitHub homelab-komodo              ← menneskelesbar, versjonert sannhetskilde
  pc6-ct103-n8n/
    README.md                      ← peker til workflowene + docs
    workflows/*.json               ← importbar eksport, UTEN hemmeligheter
    docs/*.md                      ← én doc per workflow
  docs/operations/n8n-workflows.md ← dette dokumentet
```

n8n er den levende instansen; Git er arkiv og gjenopprettingskilde. En endring
gjort kun i n8n-GUI-en lever på disk i `/opt/n8n` og forsvinner ved en
gjenoppretting — derfor skal enhver meningsfylt endring også havne i Git.

## Sikkerhet: hemmeligheter aldri i Git

- **Ingen** API-nøkler, HA-token, SSH-nøkler eller interne passord i
  `workflows/*.json` eller noe annet sted i repoet.
- Eksporten bytter ut de to hemmelighetene med stedsmarkører
  (`REDACTED_AUDIT_TOKEN`, `REDACTED_HASS_TOKEN`). Ved import settes de fra
  n8n credentials/Secrets.
- `.gitignore` ekskluderer allerede `.env`, `.env.*`, `*.key`, `*.pem`.
  Hold alle ekte verdier i Hermes `.env` på CT157 (`AUDIT_TOKEN`), i Komodo
  Stack Environment, eller i n8n credentials.
- **Mønsteret som brukes:** n8n holder *ingenting* hemmerlig. Den kaller
  Hermes-endepunktet på CT157 (`10.0.0.135:9118`), som eier alle homelab-
  nøklene og eksponerer bare resultatet. n8n trenger bare *én* token
  (`X-Audit-Token`) for å få tilgang, og *én* HA-token for å pushe. Dette er
  med hensikt: minst-privilegium, og hemmelighetene lever på ett sted.

## Prinsipper for automasjoner

1. **Diagnose før handling.** En workflow leser og varsler; den endrer ikke
   nettverk, brannmur eller lagring uten eksplisitt vedtak. Reparasjon er et
   forslag i meldingen, ikke et automatisk inngrep.
2. **Idempotens og dedup.** En feil varsles når den *oppstår*, ikke ved hver
   kjøring. Deduplikering ligger i endepunktet (state-fil), ikke i n8n, slik
   at flere workflow-er kan dele samme grunnlag uten dobbeltvarsling.
3. **Stille når ingenting har endret seg.** Dagsrapporten sender alltid; den
   timevise grenen sender kun ved `new_problems > 0`. Ingen daglig «alt OK»-
   støy.
4. **Frekvens matcher risiko.** Service-watch hver 20. min, nettverksstatus
   timevis, full diagnose daglig. Overlappende vakter er en lukt (WAN- og
   ARP-vakten var overflødige fordi service-watch dekket dem).
5. **Varsling i nivåer.** KRITISK → telefon (iPhone), ADVARSEL → nettbrett
   (iPad). Vedvarende kritisk (over 24 t) får egen påminnelse.

## Gjenoppretting (kort)

1. Import av JSON: `Workflows → Import from File`, velg filen i `workflows/`.
2. Sett inn de to hemmelighetene (se workflowens egen doc under
   «Gjenoppretting»).
3. Aktiver (import gir inaktiv workflow; aktivering er et eget steg).

Fullstendig steg-for-steg ligger i hver workflow-doc, ikke her.

## Avhengigheter utenfor n8n

- **`homelab-audit.service`** på CT157 (`10.0.0.135:9118`) — eksponerer
  `/audit`, `/network`, `/network/status`, alle bak `X-Audit-Token`.
- **Home Assistant** på pc8 (`10.0.0.7:8123`) — `notify`-tjenestene
  `mobile_app_1_iphone_r` og `mobile_app_roger_sin_ipad_mini`.
- **Hermes `.env`** — `AUDIT_TOKEN` og `HASS_TOKEN` er kilden for de to
  stedsmarkørene.