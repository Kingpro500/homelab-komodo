# Legacy-workflows – credentialstatus

## Omfang

Dette dokumentet gjelder fire deaktiverte n8n-workflows som ikke inngår i den aktive homelab-overvåkingen.

| Workflow | Status | Credentialstatus | Tiltak |
|---|---|---|---|
| Emby – overvåking og autorestart | Deaktivert | Audit-credential migrert live | Token bør roteres; workflow skal ikke aktiveres uten stream-sikkerhet |
| Homelab – tjenester nede | Deaktivert | Audit-credential migrert live | Behold deaktivert; funksjonen overlapper med nyere diagnose |
| GJELD 1 – Trekk ut gjeldstall fra Paperless | Deaktivert | Paperless/OpenRouter credentials ikke opprettet | Krever eksplisitte credentials før eventuell bruk |
| GJELD 3 – Paperless til gjeldsprogrammet | Deaktivert | Paperless/Gjeld credentials ikke opprettet | Krever eksplisitte credentials før eventuell bruk |

## Sikkerhet

Eksportene er secrets-scrubbet. Ingen tokenverdi skal legges i Git eller dokumentasjon. De gamle hardkodede verdiene i live n8n må behandles som eksponerte og roteres dersom de fortsatt er gyldige.

## Beslutning

Ingen av workflowene skal aktiveres automatisk. Paperless- og gjelds-workflowene skal enten få nye, navngitte credentials eller arkiveres etter manuell beslutning. Emby-workflowen må i tillegg verifisere aktive streams/transkoding før eventuell kontrollhandling.
