# Hermes-kø (`hermes-ko`)

Arbeidsdeling: Claude planlegger og legger oppgaver i en n8n-kø. Hermes utfører dem
uten at noen må sitte og godkjenne, og en annen modell kontrollerer arbeidet.

| Steg | Hvem | Hva |
| --- | --- | --- |
| Forslag | `gpt-5.6-luna` via Codex-abonnementet | Leser tilstanden og foreslår nøyaktig endring og tilbakerulling |
| Vurdering | Hermes sin standardmodell | Godkjenner eller avviser forslaget. To avvisninger parkerer oppgaven |
| Godkjenning | Claude eller Roger | Bare for oppgaver lagt inn med `"godkjenning": "claude"` |
| Utføring | `gpt-5.6-luna`, `--yolo` | Gjennomfører det godkjente forslaget |
| Kontroll | Fast kommando | Avgjør om oppgaven er ferdig. Ett retteforsøk ved feil |
| Sluttvurdering | Hermes sin standardmodell | Sjekker at det som ble gjort er det som ble godkjent |

Én oppgave om gangen. Når køen er tom, sendes ett varsel via `homelab-alerts`.

## Deler

| Fil | Installeres som |
| --- | --- |
| `hermes_ko.py` | CT130 `/home/hermes/.hermes/scripts/hermes_ko.py` (eier `hermes`, 0755) |
| `ko-n8n.js` | Koden i Code-noden «Kø» i n8n-workflowen `hermes-ko`; kopi ved siden av skriptet |
| `hermes-ko.service`, `hermes-ko.timer` | CT130 `/etc/systemd/system/`, `systemctl enable --now hermes-ko.timer` |

Første oppsett: `hermes_ko.py setup-n8n` lager tokenet `~/.hermes/ko.env` (0600), n8n-credentialen
`hermes-ko token` (Header Auth, `X-Ko-Token`) og workflowen. Tokenet ligger aldri i Git.

## Bruk (som `hermes` på CT130)

```sh
python3 ~/.hermes/scripts/hermes_ko.py list
python3 ~/.hermes/scripts/hermes_ko.py get k3          # forslag, vurdering, resultat
python3 ~/.hermes/scripts/hermes_ko.py approve k3      # slipp et forslag videre til utføring
python3 ~/.hermes/scripts/hermes_ko.py reject k3 "hva som må endres"   # nytt forslag
python3 ~/.hermes/scripts/hermes_ko.py add < oppgave.json
touch ~/.hermes/ko/STOPP                                # nødstopp; fjern filen for å starte igjen
```

Oppgave: `{"tittel": "...", "oppgave": "mål, fakta, nøyaktig endring, tilbakerulling", "kontroll": "<bash, exit 0 = ferdig>", "godkjenning": "ai" | "claude"}`.
Kontrollkommandoen kjøres fra CT130 som `hermes`.

`PAUSE` inneholder tidspunktet pausen utløper og grunnen til at køen venter.
`PAUSE` kan slettes for hånd for å starte køen igjen.
Ved eneste kritiske funn `map:dirty` kontrolleres kartet selv med `ssh pc6 'pct exec 120 -- git -C /opt/moved-services/nettkart-repo status --short'`; tom utskrift er et utdatert funn.

ct-ops-regelen instruerer om 200 sekunders tidsgrense, venting og inntil tre forsøk ved blokkering eller timeout.
Claude-avgjørelser videresendes nå til forslag, kontrollør, utfører og sluttvurdering.

Lokal AI-forhåndssjekk sammenligner forslag med nummererte steg før kontrolløren.
Den gjelder bare forsøk 1 og oppgaver med en linje som er nøyaktig `Steg:`.
Hvis Ollama ikke svarer, går køen videre uten forhåndssjekken.

## Statuser

`ny` → `kjorer` → (`venter_godkjenning` → `godkjent` →) `ferdig` | `ferdig_med_merknad` (kontrollen gikk, kontrolløren
hadde innvendinger) | `feilet` | `parkert` (forslaget avvist to ganger).

## Grenser

De faste reglene står i `REGLER` i skriptet: aldri Emby, aldri OPNsense-konfigurasjon, ingen sletting eller
oppretting av CT-er, ingen endring av passord, nøkler eller tokens. Køen kjører Hermes med `--yolo`, så
webhooken krever token, og bare oppgaver med en smal beskrivelse og en kontrollkommando skal legges inn.
