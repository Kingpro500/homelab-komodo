# CT reconcile orchestrator — generisk VMID-jobb

## Formål

Denne workflowen tar imot et CT-nummer (`vmid`) og sender en validert jobb til
Hermes-runneren. Den er ikke hardkodet til CT140 eller en bestemt applikasjon.
Hermes-runneren skal oppdage node, IP, hostname, tjenesteprofil, GitHub-path og
Komodo-identitet fra ferske autoritative data.

## Input

POST til n8n-webhooken `/webhook/ct-reconcile`:

```json
{
  "vmid": 140,
  "requested_action": "reconcile",
  "start_policy": "approval_required"
}
```

`vmid` er obligatorisk og må være et heltall mellom 100 og 999999. Tillatte
handlinger er `inspect`, `reconcile`, `deploy` og `repair`. `start_policy` er
`never` eller `approval_required`; standarden krever approval før en stoppet
CT startes.

Eksempel for neste jobb:

```json
{"vmid": 220}
```

## Ansvarsdeling

- **n8n:** webhook, inputvalidering og levering til runner.
- **Hermes-runner:** durable state, lease, Proxmox-discovery, profiloppslag,
  GitHub/Komodo-operasjoner, polling, retry og sluttverifikasjon.
- **Proxmox:** autoritativ kilde for VMID, node, type, status, hostname og IP.
- **GitHub/Komodo:** verifiserte kilder for repository, compose-path og ownership.

Workflowen skal ikke bruke Execute Command eller interpolere brukerinput i
shell-kommandoer. Credentials skal ligge i n8n Credentials eller runnerens
runtime-miljø, aldri i denne eksporten.

## Runner-kontrakt

`POST http://10.0.0.135:9118/ct-reconcile` skal være en fast, autentisert
adapter-endpoint. Den må returnere en jobbkvittering, ikke late som om hele
jobben er ferdig etter HTTP 200. Runneren skal fortsette jobben durabelt og
returnere/lagre én av:

- `DONE`
- `WAITING_APPROVAL`
- `RETRY_WAIT`
- `BLOCKED`

Polling og status-endepunkt implementeres i runneren før workflowen aktiveres.

## Sikkerhet og idempotens

- Jobbnøkkel er `ct:{vmid}:{action}`.
- Samme VMID/action får én aktiv lease.
- Callerens node, IP, status og hostname stoles ikke på; alt verifiseres fra
  fersk Proxmox-inventory.
- Ingen sletting, reinstallasjon, host-restart eller tvungen CT-start uten
  policy/approval.
- Ingen suksess basert på bare HTTP 200 eller utstedt Proxmox-/Komodo-task.
- Grønt nettverkskartlys krever ferdig runtime- og Komodo-verifikasjon.
- Stoppede mål bruker eksisterende rødt lys; ingen ekstra «stoppet»-tekst.

## Import og drift

1. Importer `workflows/ct-reconcile-orchestrator.json` i n8n.
2. Konfigurer autentisering som en n8n Credential på HTTP-noden eller via
   runnerens autentiserte runtime-miljø; legg aldri tokens i workflow-JSON.
3. Implementer og test `/ct-reconcile`-runneren med en ufarlig `inspect`-jobb.
4. Verifiser state, lease, dedup, timeout og secret-redaksjon.
5. Aktiver først etter en ekte test som viser fersk Proxmox-discovery.

## Ikke ferdig ennå

Selve n8n-eksporten er opprettet, men runner-endpointen og durable job-store
må bygges og testes før denne workflowen kan regnes som produksjonsklar.
