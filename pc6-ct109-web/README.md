# pc6-ct109-web — nginx for nettverkskartet

Komodo-stacken heter `pc6-ct120-web` og kjører på CT120 (`10.0.0.124`, pc6).
Den serverer nettverkskartet på `http://10.0.0.124:3020/`.

## Viktig: kartet ligger ikke her

| Hva | Hvor |
| --- | --- |
| Kilde (eneste) | Gitea, `CT120:/opt/moved-services/nettkart-repo/docs/network-map/` |
| Publisering | `/usr/local/sbin/nettkart-publish` på CT120 |
| Webrot (nginx leser) | `CT120:/srv/nettkart/www` — utenfor alle Git-kopier |
| Denne stacken | bare `nginx:alpine` + `default.conf` |

Webroten ble flyttet ut av Komodo-checkouten 10. nov 2026. Før det lå den i
`docs/network-map/` i denne Git-kopien, og en PullStack kunne overskrive det levende
kartet med en gammel GitHub-kopi. Legg derfor **aldri** kart-HTML i GitHub.
Drift-vakten (`pc7-ct130-hermes/drift-vakt/`) slår kritisk alarm hvis `docs/network-map/`
dukker opp i GitHub igjen, eller hvis nginx ikke monterer `/srv/nettkart/www`.

## Endringer i stacken

En endring i `docker-compose.yml` eller `default.conf` merges i GitHub og deployes med
Komodo (`PullStack` + `DeployStack` på `pc6-ct120-web`). Det påvirker ikke kartinnholdet.

## 13. november 2026 — denne nginx-en serverer et gammelt kart

Stacken kjører en `nettkart`-container i CT210 på `http://10.0.0.128:3020`, med
webrot `/opt/komodo/stacks/pc6-ct109-web/docs/network-map`. Innholdet der er
fra 23. oktober 2026.

**Det ekte nettverkskartet kjører i CT120 på `http://10.0.0.124:3020`** og
oppdateres av `nettkart-publish` fra Gitea-arbeidskopien i
`/opt/moved-services/nettkart-repo`. Den som åpner .128-adressen får altså et
kart som er en måned gammelt, uten å se at det er feil versjon.

Denne stacken bør bort, men er ikke slettet: det er Rogers avgjørelse, og en
sletting av en kjørende stack kjører `compose down` på CT-en.

## Nyheter — `http://10.0.0.124:3020/nyheter/` (lagt til 28. nov 2026)

Egen nyhetsside for Roger: toppsakene per land, med overskrifter på andre språk
enn norsk, svensk, dansk og engelsk maskinoversatt til norsk.

| Del | Hvor |
| --- | --- |
| Siden | `nyheter/index.html` (montert i nginx som `/nyheter/`) |
| Land og aviser | `nyheter/feeds.json` — rediger her, og deploy stacken |
| Henter | containeren `nyheter` (`python:3.13-alpine`, kun standardbibliotek), `nyheter/fetch.py`, hvert 30. min |
| Data | Docker-volumet `nyheter-data` (`data.json`, oversettelsescache, funne RSS-adresser) — monteres read-only i nginx som `/nyheter/data.json` |

- **Toppsaker:** Google News sin forside per land (rangert etter hvor store sakene er i lokale medier). Danmark har ingen egen Google-utgave og bruker et søk i de største danske mediene.
- **Dine aviser:** nyhetsmappene i Rogers Chrome-bokmerker (`N/…`). Tjenesten finner RSS-feeden fra forsiden; aviser uten åpen RSS (eller som blokkerer) hentes via Google News-søk på eget domene og merkes «via søk».
- **Ståsted:** hver avis har `lean` i `feeds.json` (omtrentlig, etter AllSides/Ad Fontes/MBFC der det finnes, ellers allmenn oppfatning).
- **Oversettelse:** `clients5.google.com` (gratis, uten nøkkel), med MyMemory som reserve. `translate.googleapis.com` er blokkert fra hjemmenettet («Sorry»-side). Kall til `news.google.com` strupes til minst 2 s mellomrom.
- Første henting etter en tom cache tar ca. 6–7 minutter; siden viser «Fant ingen data ennå» så lenge.
