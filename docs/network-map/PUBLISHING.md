# Trygg publisering av nettverkskartet

## Regel

`origin/main` er den eneste publiseringskilden. Ingen skal kopiere en lokal
eller tilfeldig serverfil rett til den levende siden. Dette er spesielt viktig
etter at en ufullstendig v2.014-fil erstattet den komplette kart-layouten.

Den aktive nginx-containeren `nettkart` kjører i **CT120** (`10.0.0.124`) og
serverer bind-mounten:

`/opt/moved-services/nettkart-repo/docs/network-map` →
`/usr/share/nginx/html` (read-only i containeren).

CT120 er den renummererte tidligere CT104. Se
[`id-renumbering-2026-10-21.md`](../id-renumbering-2026-10-21.md) for hele
ID-mappingen.

## Kontrollert publisering

Kjør kun dette på CT120 etter at en kartendring er reviewet og pushet til
GitHub:

```sh
cd /opt/moved-services/nettkart-repo
bash scripts/deploy-network-map.sh
```

Skriptet henter `origin/main`, validerer at kandidaten har:

- versjonsnummer;
- full serviceoversikt;
- VM/CT-rammer (`data-vmid`);
- det pålagte node-sammendraget og `/nodes`-integrasjonen.

Det nekter også å publisere lavere versjon enn den levende siden. Før hver
publisering lagres den nåværende live-filen i
`/var/lib/nettkart/backups/` på CT120. Nginx trenger ikke restart fordi den
leser den erstattede statiske filen på neste HTTP-kall.

## Komodo

Komodo kan brukes til å kjøre den samme kommandoen som en kontrollert deploy-
handling på CT120. Den skal peke på dette Git-repoet og kjøre skriptet over —
ikke kjøre `cp`, `git reset --hard`, eller synkronisere en lokal arbeidskopi.
Før en Komodo-stack eller prosedyre opprettes må den verifiseres mot den
eksisterende `nettkart`-containeren, slik at den ikke oppretter en konkurrerende
container på port 3020.
