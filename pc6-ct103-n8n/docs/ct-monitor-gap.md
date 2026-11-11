# CT-overvåking: nye CT-er uten kart eller SmokePing

**Live n8n:** `CT-opprettelse: kart og SmokePing gapvarsel` (`tcGXngBIsipFnbv0`), aktiv. Timeplan: hver time; manuelt testkall: `POST /webhook/ct-monitor-gap`.

## Hva den gjør

Leser Proxmox-klyngens gjesteliste med eksisterende **lese-credential** i n8n, live nettverkskart og SmokePing `Targets` fra GitHub `main`. Første vellykkede kjøring etablerer baseline og varsler ikke om eksisterende CT-er. Senere nye CT-er som mangler `data-vmid` i kartet eller `++ Ct<vmid>` i SmokePing varsles én gang via `homelab-alerts`; ingen varsling når alt er i orden. Workflowens statiske data lagrer kjente ID-er, utsendte funn og siste skanning. Dersom Proxmox-/kart-/Targets-svar er ufullstendig, feiler kjøringen uten å oppdatere baseline. Gjenbruk av en slettet VMID kan oppdages når ID-en har vært ute av en vellykket skanning.

**Begrensning:** Denne flyten *varsler* om manglende registrering; den skriver ikke GitHub, deployer ikke Komodo og publiserer ikke nettverkskartet automatisk. Det er tilsiktet: en tom CT har ingen kjent applikasjonsprofil, og en Compose-fil må ikke oppfinnes. Eksisterende `NetBox – opprett nye Proxmox-CT-er` er en separat timesynk for NetBox, ikke dette kart-/SmokePing-varselet. Kartpublisering følger Gitea/CT120 og `nettkart-publish`; SmokePing-targets følger GitHub PR og Komodo-deploy.

CT121 på pc6 (10.0.0.226) er allerede lagt inn i både live kart og SmokePing. Den har Docker-Periphery og Komodo-server `pc6-ct121-ct121` Ok, men ingen applikasjonsstack; **ikke kjør `ct-komodo 121` på nytt bare fordi Compose-mappen mangler**. Når den får en faktisk tjeneste, opprettes tjenestens Compose/README i GitHub og stacken bindes til samme server-ID etter verifisering.

## Gjenoppretting og test

Eksport: [`../workflows/ct-monitor-gap.json`](../workflows/ct-monitor-gap.json). Importer uten hemmeligheter; knytt `Proxmox-inventar` til eksisterende n8n-credential `Proxmox inventory read (n8n)` (lesetilgang). Ingen tokenverdier i eksporten. Aktiver og kjør POST-webhook. GET siste execution med `includeData=true`; kontroller at Proxmox- og Code-node lyktes. Første kjøring returnerer tomt varsel og initialiserer baseline. Lokal scenetest bekreftet baseline, ett varsel for ny manglende CT, deduplisering og rydding når begge oppføringer finnes. Ingen virkelig ny CT er opprettet bare for å teste varselbanen; faktisk telefonlevering for en ny CT er derfor ikke verifisert.
