# Hermes AI Matrix-bot

## Formål

Matrix-botten `@hermes-ai:matrix.lan.local` gir en kontrollert tekstbasert inngang til status fra Home Assistant og til utvalgte Sonos- og lysfunksjoner. Botten er uavhengig av lokal Ollama for Home Assistant-, Sonos- og lysregler.

## Arkitektur

```text
Element / Matrix
        |
        v
Synapse + hermes-ai-matrix.service
CT180 · pc6 · 10.0.0.120
        |
        +--> Home Assistant 10.0.0.7:8123
        |       +--> Sonos Arc
        |       +--> stuelampe
        |       +--> sensorer
        |
        +--> Ollama 10.0.0.133:11434
                (kun for fritekst/lokal AI når tilgjengelig)
```

PC1/Ollama kan være avslått under gaming. Matrix, Synapse og Home Assistant skal derfor fungere uten PC1. Det finnes ingen automatisk Hermes-fallback til Ollama.

## Runtime

| Element | Verdi |
|---|---|
| Matrix-vert | CT180 på pc6 |
| Matrix-adresse | `10.0.0.120` |
| Tjeneste | `hermes-ai-matrix.service` |
| Aktiv botfil | `/opt/synapse/hermes_ai_matrix.py` |
| Home Assistant | `http://10.0.0.7:8123` |
| Ollama | `http://10.0.0.133:11434` |
| Matrix-rom | `[REDACTED]` |
| Matrix-bot-token | `[REDACTED]` |
| Home Assistant-token | `[REDACTED]` |

Tokens og andre credentials skal ligge i runtime-secrets, aldri i Git.

## Modeller og fallback

- Codex er primærmodell for Hermes.
- Automatiske fallback-providere er fjernet.
- Aliaset `local-qwen8` peker manuelt til Ollama-modellen `qwen3:8b`.
- Qwen brukes ikke automatisk når PC1/Ollama er utilgjengelig.
- Feil mot Ollama på `10.0.0.133` rapporteres som at lokal AI er utilgjengelig. Home Assistant-feil gir en separat feiltekst.

## Tillatte Home Assistant-entiteter

### Lesing

- `sensor.pc1_ai_power` — PC1-strøm
- `sensor.stue_2_temperatur` — stuetemperatur
- `media_player.stue_arc_sonos` — Sonos Arc-status
- `light.stue` — stuelampe-status

### Styring

- `media_player.stue_arc_sonos`
- `light.stue`

Disse entitetene skal ikke styres av botten:

- `light.stue_go`
- `light.stue_play`

Ingen frie Home Assistant-tjenestekall skal bygges fra modelltekst. Kommandoer må treffe faste regler i botkoden.

## Sonos Arc

Entitet:

```text
media_player.stue_arc_sonos
```

Støttede funksjoner:

- status og hva som spilles
- play
- pause/stopp
- neste spor
- forrige spor
- mute/unmute
- absolutt volum i prosent
- relativt volum opp/ned
- kildevalg

Eksempler:

```text
Sett arc 32
Sett lydnivået til 40 prosent på Sonos Arc
Skru opp lyden
Skru ned lyden
Pause Sonos Arc
Neste spor
Forrige spor
Hva spilles på Sonos?
```

Volum og kilde leses tilbake fra Home Assistant etter et kall. Botten skal ikke bekrefte en ønsket verdi dersom faktisk state ikke viser endringen.

Kildevalg valideres mot Arcens `source_list`. `TV` er verifisert fungerende. `Daily Mix 1` finnes i listen, men ga HTTP 500 og Arc beholdt `TV`; denne kilden skal derfor regnes som uavklart/ikke fungerende inntil integrasjonen er undersøkt.

## Lys

Godkjent entitet:

```text
light.stue
```

Støttede funksjoner:

- slå på
- slå av
- status
- lysstyrke i prosent, begrenset til 1–100

Etter på/av og lysstyrke leses faktisk Home Assistant-state tilbake. Bekreftelsen skal bare sendes dersom state viser forventet resultat.

## Matrix-behandling

- Botten ignorerer meldinger fra seg selv.
- Matrix-eventer dedupliseres med `event_id`.
- Kun relevante `m.room.message`-eventer behandles.
- Taleeventer (`m.audio`) behandles eksplisitt.
- Talegjenkjenning er ikke aktivert. Botten skal ikke sende lyd ukritisk til lokal AI.

## Sikkerhetsmodell

- Ingen PC1-restart eller strømstyring er eksponert.
- Ingen Proxmox-kall er eksponert.
- Ingen automatisk oppstart av PC1 eller Ollama.
- Sonos- og lysstyring er begrenset til entiteter og tjenester som er kodet eksplisitt.
- Local Qwen får ikke frie skrive-, restart-, strøm- eller kontrollkall.
- Secrets skal aldri kopieres til dokumentasjon eller commit.

## Drift og verifikasjon

Sjekk tjenesten på CT180:

```bash
systemctl is-active hermes-ai-matrix.service
systemctl status hermes-ai-matrix.service --no-pager
journalctl -u hermes-ai-matrix.service -n 100 --no-pager
python3 -m py_compile /opt/synapse/hermes_ai_matrix.py
```

Fra Proxmox-verten brukes `pct exec 180 -- ...`.

Ved endringer skal aktiv fil først hentes/inspeksjoneres, fordi tidligere arbeidskopier i `/tmp` har vært borte eller foreldet. Verifiser syntaks før deploy, restart tjenesten og les tilbake `systemctl is-active` og journalen.

## Deploy og rollback

Kildekoden skal ligge i dette Git-repositoriet under `docs/` for dokumentasjon. Selve Matrix-botfilen er foreløpig runtime-deployet i CT180 og er ikke ennå etablert som en versjonskontrollert Komodo-stack.

Fremtidig permanent løsning bør:

1. legge botkoden i en egen repo-mappe/stack
2. lagre secrets i runtime/Komodo Environment
3. deploye gjennom Komodo/GitOps
4. verifisere tjeneste, journal og Matrix `/sync`
5. rulle tilbake til forrige commit ved feil

Manuell rollback av dagens runtime gjøres ved å gjenopprette forrige validerte `/opt/synapse/hermes_ai_matrix.py`, kjøre `py_compile`, restarte tjenesten og verifisere `active`.

## Kjente begrensninger og gjenstående arbeid

- Spotify-/favorittkilder er ikke ferdig løst; `Daily Mix 1` returnerte HTTP 500.
- Talegjenkjenning er ikke implementert.
- Parseren mangler automatiserte enhetstester.
- Full end-to-end-test fra vanlig Element-klient for alle kommandoer bør gjennomføres.
- Botkoden bør flyttes fra manuell runtime-deploy til versjonskontrollert deploy.
- Dokumentasjonen beskriver ikke credentials eller konkrete tokenverdier.
