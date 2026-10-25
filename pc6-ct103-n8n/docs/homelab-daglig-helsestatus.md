# Homelab – daglig helsestatus

- **Workflow-ID:** `1yLU74fLwugB8j79`
- **Status:** deaktivert historikk-workflow
- **Trigger:** daglig kl. 20:00
- **Kilde:** `http://10.0.0.135:9118/audit`
- **Varsling:** audit-adapterens `/notify`

## Hva den gjør

Workflowen henter audit-status, vurderer om `KRITISK` eller `ADVARSEL` er større enn null, og sender en kort melding med de fem øverste vedvarende kritiske funnene.

Workflowen er fortsatt deaktivert og er ikke en del av den aktive varslingskjeden. Den beholdes som historikk fordi den overlapper med den aktive `Daglig homelab-diagnose`.

## Credential-håndtering

Audit-headeren ligger i n8n-credentialen `Homelab Audit Header`. Eksporten inneholder ingen token. Credentialen må finnes før import eller gjenoppretting.

## Verifisering

- Live GET viste `active: false`.
- `Hent audit` bruker `httpHeaderAuth`-credential.
- Varslingsnoden bruker samme credentialtype for audit-adapteren.
- Audit-endepunktet svarte HTTP 200 med gjeldende sammendrag: 1 kritisk, 12 advarsler og 2 informasjonsfunn.

## Begrensninger

Ingen aktivering, sletting, restart eller automatisk opprydding er gjort. Workflowen bør ikke aktiveres parallelt med den aktive daglige diagnosen uten først å fjerne overlappende varsler.
