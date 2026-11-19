# Pinchflat – tilgjengelighetsvakt

Hvert 5. minutt: `GET http://10.0.0.164:8945/` (CT172 pc6). Varsler bare ved overgang (nede/oppe) via
`homelab-alerts`, som videre går til [varsel-digest](varsel-digest.md).

**Rettet 19. nov 2026:** Code-noden brukte `fetch()`, som ikke finnes i n8n-sandkassen. Hver sjekk
feilet med «fetch is not defined» og ga falsk «Pinchflat er utilgjengelig» hvert 5. minutt fra
18. nov 02:20 (477 hendelser, 27 push). Bruker nå `this.helpers.httpRequest` som de andre vaktene.
Regel: i n8n Code-noder, bruk `this.helpers.httpRequest`, aldri `fetch()`.

Eksport: [workflows/pinchflat-tilgjengelighetsvakt.json](../workflows/pinchflat-tilgjengelighetsvakt.json)
