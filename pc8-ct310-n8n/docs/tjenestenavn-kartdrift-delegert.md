# Tjenestenavn og kartdrift – delegert diagnose

Workflowen gjør ikke direkte endringer i nettverk, DNS eller kart.

## Flyt

1. Daglig trigger eller webhook `/webhook/tjenestenavn-kartdrift`.
2. Validerer tjenestenavn/VMID og lager deterministisk jobb-ID.
3. Sender en begrenset diagnoseplan til lokal Ollama på CT156.
4. Legger resultatet i `hermes-ko`.
5. Hermes utfører eventuell kontrollert handling og må lese tilbake resultatet.

## Tillatte mål

- DNS-/DHCP-status
- DNS-oppslag fra relevante VLAN
- tjenestehelse via tjenestenavn
- IP-adresser i kart- og brukerlenker
- kartstatus og versjonslogg

## Sikkerhetsregler

- Ingen frie shell-kommandoer fra webhook-input.
- Ingen IP-adresser i brukerlenker.
- Ingen credentials i eksporten.
- Røde driftsfunn skal stoppe flyten.
- Workflowen skal være inaktiv til lokal test og en faktisk n8n-execution er verifisert.

## Gjenoppretting

Importer `workflows/tjenestenavn-kartdrift-delegert.json`, kontroller credentialen `hermes-ko token`, kjør lokal Code-test og én kontrollert execution før aktivering.
