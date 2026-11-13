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
