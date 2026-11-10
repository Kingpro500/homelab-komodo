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
