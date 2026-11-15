# Komodo-duplikatvakt

Rød vakt hvert 10. minutt og webhook `/webhook/komodo-duplicate-identity`. Den korrelerer Proxmox VMID med alle Komodo-servere og rapporterer servernavn, server-ID, status, stack-antall, Proxmox-node/VMID og `connect_as`.

Samme numeriske CT-ID på to eller flere forventede aktive Komodo-servere er alltid `critical`, aldri gul/grønn. Incident-ID er deterministisk over VMID og server-ID-er. Det sendes kun read-only klassifisering til Hermes; uklar eier stopper all reparasjon. Ingen automatisk sletting, flytting, overtakelse eller rename.

Live n8n-ID og aktiv status må leses fra autorisert n8n API før import/oppdatering. Git-eksportens metadata er ikke bevis på runtime-aktivering.

## Scenetester

    node scripts/test_komodo_duplicate_identity.js

Dekker ingen duplikat, ett duplikat, flere duplikater, `NotOk`-server og stack til stede.
