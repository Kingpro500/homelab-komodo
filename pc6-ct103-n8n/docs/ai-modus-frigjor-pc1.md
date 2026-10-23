# AI-modus – frigjør PC1

## Formål

Frigjør ressurser på PC1 når Ollama/Hermes bruker RTX 3070.

## Trigger

- `POST http://10.0.0.119:5678/webhook/ai-start`
- `POST http://10.0.0.119:5678/webhook/ai-stop`

Workflow-ID i n8n: `TVxIF3OGvWTOVdVW`.

## Atferd

`ai-start` stopper CT102 på pc1 (`ct116-pihole`). CT105 og CT150 er allerede
stoppet og berøres ikke. AI-containeren CT350 (`ct156-ollama`) stoppes aldri.

`ai-stop` starter CT102 igjen.

Tre Pi-hole-instanser finnes i miljøet, så én stoppet instans gir DNS-failover.
Hvis DNS-failover senere viser seg utilstrekkelig, skal workflowen endres til
å stoppe en annen reserveinstans i stedet — ikke stoppe alle tre.

## Avhengigheter og sikkerhet

Workflowen bruker det eksisterende avgrensede `homelab-audit`-kontrollendepunktet
på `10.0.0.135:9118`, ikke shell-kommandoer eller klientstyrte VMID-er.
Audit-tokenet ligger kun i n8n og er erstattet med `REDACTED_AUDIT_TOKEN` i
Git-eksporten.

## Bruk

1. Kall `ai-start` før tung lokal AI-bruk.
2. Kall `ai-stop` etterpå for å starte Pi-hole tilbake.
3. Bekreft i nettverkskartet eller med DNS-oppslag at minst to Pi-hole-
   instanser fortsatt svarer.

## Gjenoppretting

Importer `workflows/ai-modus-frigjor-pc1.json`, legg inn audit-tokenet som
n8n-secret/header, aktiver workflowen og test først med `ai-start` og deretter
`ai-stop`. Verifiser at CT102 faktisk går `running -> stopped -> running`.
