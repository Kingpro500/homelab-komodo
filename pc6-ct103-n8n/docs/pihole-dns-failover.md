# Pi-hole DNS-failover

Workflowen kjører hvert minutt og ber Hermes (`10.0.0.135`) teste en direkte DNS-respons fra begge Pi-hole-instansene. Den tester `homeassistant.lan.local`, så en vellykket test bekrefter både Pi-hole, Unbound og lokal DNS-resolusjon.

Tre påfølgende målinger uten svar fra **begge** Pi-hole-instansene setter Kea DHCP option 6 til `10.0.0.1` (Unbound). Tre påfølgende friske målinger fra minst én Pi-hole setter den tilbake til `10.0.0.115,10.0.0.116`.

Kea-endringen påvirker nye DHCP-leaser umiddelbart, men eksisterende klienter tar den ved lease-fornyelse. Nødmodus redder derfor nye og fornyede klienter og hindrer at et langt Pi-hole-avbrudd blir permanent; den kan ikke tvinge alle eksisterende enheter til å hente en ny lease. Varslet forklarer når et manuelt lease-fornyelse eller et Wi-Fi-av/på kan være nødvendig.

## Sikkerhetsmodell

Kun Hermes har OPNsense API-nøklene. n8n har bare `X-Audit-Token` for Hermes og en Home Assistant-token for push-varsel. Hermes får bare endre DNS-feltet på LAN-subnetten `10.0.0.0/24`; den endrer ikke brannmurregler, Unbound eller andre DHCP-verdier.

## Deploy og gjenoppretting

1. Installer `hermes/dns_failover.py` som `/home/hermes/.hermes/scripts/dns_failover.py` på CT157.
2. Oppdater `homelab_audit_server.py` på CT157 med endepunktene `GET /dns/status` og `POST /dns/reconcile`, og restart `homelab-audit.service`.
3. Importer `workflows/pihole-dns-failover.json` i n8n, erstatt `REDACTED_AUDIT_TOKEN` og `REDACTED_HASS_TOKEN` med eksisterende secrets, og aktiver workflowen.
4. Bekreft normalt svar med `GET /dns/status`, og test en simulert failover bare i et vedlikeholdsvindu.

Workflowen sender kun ved failover, tilbakeføring eller API-feil; den er stille når DNS-tilstanden er uendret.
