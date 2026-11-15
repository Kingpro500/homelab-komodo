# Komodo-duplikatvakt

Rød vakt hvert 10. minutt og webhook `/webhook/komodo-duplicate-identity`. Sammenligner Proxmox VMID med Komodo ListServers. Duplikater dedupliseres av incident-ID i downstream alarm, varsles rødt og sendes til Hermes som read-only klassifisering. Ingen automatisk destruktiv opprydding; eierskap må klassifiseres og eksplisitt godkjennes før endring.
