# Tunarr: kontrollert cache-rebuild

## Når

Brukes når `/config/tunarr/cache` vokser urimelig eller artwork/subtitle-cache
er korrupt. Dette er ikke en normal løsning på avspillingsfeil.

På PC6 CT250 var cache målt til omtrent 26 GB 2026-11-03, nesten utelukkende
`cache/subtitles`. Dette er gjenoppbyggbar cache; database, kanallinjer og
brukeroppsett ligger andre steder og skal ikke slettes.

## Forutsetninger

- Ingen aktive strømmer fra den aktuelle Tunarr-instansen.
- Fersk backup av hele den separate Tunarr-konfigurasjonen.
- NFS-mount er frisk og read-only.
- Endringen utføres gjennom Komodo ved å stoppe og starte bare den berørte
  Tunarr-stacken.

## Sikker prosedyre

1. Verifiser at Emby og den andre Tunarr-instansen er friske.
2. Ta timestampet backup av `/config/tunarr`, inkludert `db.db`.
3. Stopp bare aktuell Tunarr-container gjennom Komodo.
4. Tøm kun `/config/tunarr/cache/subtitles`.
5. Ikke rør `db.db`, `channel-lineups`, `streams`, `images` eller
   `data.ms` i samme operasjon.
6. Start samme Komodo-stack.
7. Verifiser UI, M3U, XMLTV, artwork og én HLS-strøm.
8. Overvåk diskvekst og logg tidspunkt/resultat i hendelsesloggen.

Hvis cache vekser tilbake raskt, undersøk subtitle-ekstraksjon og berørte
kanaler før ny sletting. Ikke automatiser sletting før vi har en dokumentert,
testet retensjonsmekanisme fra Tunarr.
