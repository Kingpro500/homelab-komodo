# GJELD/Paperless – legacy-workflows

Begge workflowene er deaktivert og skal ikke aktiveres uten manuell kontroll.

| Workflow | Avhengigheter | Nåstatus |
|---|---|---|
| GJELD 1 – Trekk ut gjeldstall fra Paperless | Paperless-token og OpenRouter API-key | Eksportert; secrets ikke tilgjengelige i agentmiljøet |
| GJELD 3 – Paperless til gjeldsprogrammet | Paperless-token og Gjeldsprogram-token | Eksportert; secrets ikke tilgjengelige i agentmiljøet |

## Sikkerhetsregel

Ingen tokens eller API-nøkler skal legges i Git, workflow-JSON eller dokumentasjon. Opprett navngitte n8n-credentials når verdiene er tilgjengelige via sikker manuell registrering.

## Før eventuell aktivering

1. Opprett egne n8n-credentials med minst mulig tilgang.
2. Knytt Paperless-kallet til Paperless-credentialen.
3. Knytt gjeldsimporten til egen Gjeldsprogram-credential.
4. Knytt OpenRouter-kallet til egen LLM-credential.
5. Kjør først en manuell test uten skrivehandling.
6. Verifiser at ingen data sendes til feil mottaker.
7. Aktiver ikke parallelt uten å kontrollere duplikatimport og idempotens.
