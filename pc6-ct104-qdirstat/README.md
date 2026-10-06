# qDirStat — pc6 CT104

Treemap-graf over Unraid-filsystemet (JLesage-avbildning). egnet til å finne
hva som spiser plass nede på mappenivå, mens Grafana-dashbordet `unraid-storage`
gir oversikten på disk- og share-nivå.

- **Server:** `pc6-ct104-node` (docker, NFS mot Unraid)
- **Web-GUI:** `http://10.0.0.124:5800`
- **Bilde:** `jlesage/qdirstat:latest`
- **Tilgang:** leser `/media` (Unraid media-share) via NFS, kun lesekjøring
  (`:ro`), `WEB_FILE_MANAGER=0` — kan ikke endre filer.

## Bruk

1. Åpne `http://10.0.0.124:5800` (web-GUI, ingen innlogging — binder seg til LAN i CT104).
2. Velg mappe (f.eks. `/media`) i QDirStat og kjør skann.
3. Treemap viser mappestørrelser; grønn = nylig endret, rødlig = gammel.

For å scanne andre Unraid-shares enn media, legg dem til i compose `volumes:`
(f.eks. `/mnt/user/downloads:/downloads:ro`). Monter kun lesekjøring (`:ro`),
aldri skrivetilgang til media.

## Notat om Unraid API

Unraid GraphQL er read-only — den kan lese fyllingsgrad men ikke filsystemet.
Derfor kjører QDirStat direkte mot NFS-mountet på CT104 i stedet for mot API-et.
Grafana-dashbordet bruker API-et (kapasitet/shares); QDirStat bruker filsystemet
(mapper/trefordeling).
