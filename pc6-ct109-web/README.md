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

## 28. november 2026 — den gamle tvillingstacken er fjernet

Komodo-stacken `pc6-ct109-web` i CT210 (`10.0.0.128:3020`, kart fra 23. okt. 2026) brukte samme
mappe som `pc6-ct120-web` og ble derfor også deployet ved hver endring her. Den er fjernet etter
Rogers ja (`DestroyStack` + `DeleteStack`, 28. nov 2026). Mappen deployes nå bare av `pc6-ct120-web` (CT120).
Checkout-mappen `/opt/komodo/stacks/pc6-ct109-web` i CT210 er ikke slettet.

## Nyheter — `http://10.0.0.124:3020/nyheter/` (lagt til 28. nov 2026)

Egen nyhetsside for Roger: toppsakene per land og per tema (KI, teknologi, vitenskap, utenriks/tenketanker, forsvar, økonomi, energi, Reddit/forum, Substack, faktasjekk, homelab, bil, kultur, satire), med overskrifter på andre språk
enn norsk, svensk, dansk og engelsk maskinoversatt til norsk.

| Del | Hvor |
| --- | --- |
| Siden | `nyheter/index.html` (montert i nginx som `/nyheter/`) |
| Land og aviser | `nyheter/feeds.json` — rediger her, og deploy stacken |
| Henter | containeren `nyheter` (`python:3.13-alpine`, kun standardbibliotek), `nyheter/fetch.py`, hvert 30. min |
| Data | Docker-volumet `nyheter-data` (`data.json`, oversettelsescache, funne RSS-adresser) — monteres read-only i nginx som `/nyheter/data.json` |

- **Toppsaker:** Google News sin forside per land (rangert etter hvor store sakene er i lokale medier). Danmark har ingen egen Google-utgave og bruker et søk i de største danske mediene.
- **Aviser:** nyhetsmappene i Rogers Chrome-bokmerker (`N/…`), supplert (`"added": true`) slik at hvert land har minst én avis i hver fløy: ytre venstre, venstre, sentrum, høyre, ytre høyre (+ allmenn, statlig, opposisjon). Tjenesten finner RSS-feeden fra forsiden; aviser uten åpen RSS (eller som blokkerer) hentes via Google News-søk på eget domene og merkes «via søk». Kjente hull: Iran mangler ytre venstre (finnes ikke lovlig), Midtøsten er en region uten felles skala.
- **Ståsted:** `lean` i `feeds.json` — omtrentlig, etter Wikipedia-beskrivelser og AllSides/Ad Fontes/MBFC der de finnes. I Iran, Russland og Tyrkia følger skalaen landets egne fløyer (reformister = venstre, hardlinere = ytre høyre). Siden lar Roger skjule fløyer og velge 2 eller 3 saker per avis.
- **Oversettelse:** `clients5.google.com` (gratis, uten nøkkel), med MyMemory som reserve. `translate.googleapis.com` er blokkert fra hjemmenettet («Sorry»-side). Kall til `news.google.com` strupes til minst 2 s mellomrom.
- Første henting etter en tom cache tar ca. 6–7 minutter; siden viser «Fant ingen data ennå» så lenge.
- **Tema:** `topics` i `feeds.json` (samme format som land). Siden har fanene Alle / Land / Tema.
- **Reservesøk:** kilder uten RSS søkes først i Bing News (`format=rss`, nyeste først), deretter Google News. Reddit blokkerer RSS fra hjemmenettet og hentes via Google News-søk på `reddit.com/r/<navn>`. Struping: Google News 3 s, Bing 2 s, Reddit 7 s mellom kall; søk caches i 90 min.
- Én runde med ca. 310 kilder tar ca. 8 min med tom cache, betydelig kortere etterpå. Henteren kjører 8 kilder i parallell.
- **Flere land (lagt til 28. nov 2026):** 88 land fra BNP-listene for Europa og verden, med `"tier": 2` i `feeds.json`. De vises lukket på siden og nås via nedtrekkslisten «🌐 Flere land». De hentes bare hvert 2. time (`"refresh": 7200`; mellom rundene gjenbrukes forrige resultat fra `data.json`), med 5 toppsaker og 5 saker per avis. Land uten egen Google News-utgave (`"top_lang": "en"`) bruker et engelskspråklig Google News-søk på landets navn som toppsaker. Små land og autoritære stater har ikke full fløyspredning, og bruker statlig/opposisjon der det passer.
- **Oversettelsestak:** høyst `MAX_NEW_TRANSLATIONS` (standard 700) nye oversettelser per runde. Overskrifter over taket vises på originalspråket til neste runde, så første runde etter en utvidelse ikke henger i timevis.
- **Podkaster, strømmere og bil-YouTube:** temaene `t-pod` og `t-stream` og YouTube-kanaler i `t-bil` henter kanalenes egne RSS-strømmer (`youtube.com/feeds/videos.xml?channel_id=…`, struping 1 s). Twitch har ingen åpen RSS for direktesendinger uten API-nøkkel, så strømmerne følges via YouTube-kanalene og et nyhetssøk. Jeremy Clarksons spalter (The Sunday Times, The Sun) og nyheter om Clarkson's Farm hentes via nyhetssøk; hans egne YouTube-kanaler har ingen nye videoer.
