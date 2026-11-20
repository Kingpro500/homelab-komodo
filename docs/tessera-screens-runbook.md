# Tessera-skjermer (ESP32) i Home Assistant: runbook for agenter

Gjelder Codex, Claude og Hermes. Sist verifisert live: 2026-11-20 (claude-code).

Tessera (tidligere «ESP Screens») er en Home Assistant-app som bygger ESPHome-firmware til
billige ESP32-berøringsskjermer og styrer flisene på dem. Repo:
<https://github.com/MaxGramser/homeassistant_espscreen>.

## Hva som finnes

| Ting | Verdi |
| --- | --- |
| Home Assistant | VM100 på **pc9** (`10.0.0.103`), Home Assistant OS, `http://10.0.0.7:8123` |
| Tessera-app | «Tessera Screen Manager», container `app_ec8ae0ed_esp_screen_manager` (0.4.99) |
| Tessera-data | `/data` i containeren (byggemapper, `screensavers.json`, `screens.json`) |
| ESPHome-profiler | `/homeassistant/esphome/<navn>.yaml` + `<navn>.local.yaml` (inneholder API-nøkkel og OTA-passord: aldri vis dem) |
| Port 8098 | Bilder (cover/kamera) som skjermene henter; publisert på `10.0.0.7:8098` |

| Skjerm | Brett | IP / MAC | ESPHome-navn | HA-område | HA-prefiks |
| --- | --- | --- | --- | --- | --- |
| Stue | Guition 4″ ESP32-S3-4848S040 | `10.0.0.3` / `1c:db:d4:76:da:34` | `stue` | 101 Stue | `101_stue_stue_` |
| Sov 2 | Guition 4″ ESP32-S3-4848S040 | `10.0.0.23` / `28:84:85:85:fd:30` | `sov2` | 106 Sov 2 Stort | `101_stue_sov_2_` (laget før flytting av område; ID-ene er ikke endret) |
| Stue 10 | Guition 10.1″ JC8012P4A1 (første utgave, pre-v3 P4 + C6) | `10.0.0.26` / Wi-Fi-MAC `10:20:ba:f3:c7:48` (HA-enhet `80:f1:b2:d3:95:ce`) | `stue10` | 101 Stue | `101_stue_stue_10_` |

Begge er DHCP-adresser. Kartet (Gitea, `nettkart-publish`) er fasit for IP-er.
Rutenettet er **3×5 per side på 4″ og 5×5 på 10.1″, og gjelder hele skjermen**. Sider kan ikke ha egne rutenett.
Fyll en side «luftig» med `3x1`-fliser i stedet.

## Tilgangsruter

1. **HA REST/WebSocket (foretrukket for fliser og innstillinger).**
   - Hermes: `HASS_URL` / `HASS_TOKEN` fra `~/.hermes/.env`, se [`hermes-access.md`](hermes-access.md).
   - Fra pc6 uten egen token: kjør Python inne i Tessera-containeren og bruk containerens egen
     `SUPERVISOR_TOKEN` mot `http://supervisor/core/api` (se rute 2). Skriv aldri ut tokenet.
2. **Inn i Tessera-containeren (for ESPHome, OTA, logger og profiler).** Fra pc6:
   ```bash
   ssh root@10.0.0.103 "qm guest exec 100 --timeout 60 --pass-stdin 1 -- docker exec -i app_ec8ae0ed_esp_screen_manager python3 -" < skript.py
   ```
   Svaret er JSON fra QEMU-gjesteagenten; selve utskriften ligger i `out-data`/`err-data`.
   Hold hvert kall under ca. 90 s; start lange jobber med `docker exec -d … > /data/<logg>` og les loggen etterpå.
3. **Tessera-appens eget HTTP-API (port 8099) kan ikke brukes direkte.** Det godtar bare HA-ingress
   (`172.30.32.2`) og svarer 403 ellers. Ikke prøv å omgå dette.

## Fliser: hendelsene Tessera lytter på

Tessera endrer en skjerm og sender den ut umiddelbart når disse HA-hendelsene fyres
(`POST /api/events/<hendelse>`):

| Hendelse | Bruk |
| --- | --- |
| `esp_screens_add_tile` | Ny flis: `screen`, `entity`, `name`, `page`, `row`, `column` eller `slot`, `size` (`single`, `wide`, `tall`, `square`, `full`, eller `CxR` som `3x1`, `3x2`), `controls`, `display`, `icon`, `tap`, `action`/`data` |
| `esp_screens_remove_tile` | Fjern: `entity` + `slot` (eller `page`) når entiteten finnes flere ganger |
| `esp_screens_move_tile` | Flytt: `from_slot`/`from_page` + ny `page`/`slot` |
| `esp_screens_order_tiles` | Sorter: `entities` i ønsket rekkefølge |

- Les alltid **`sensor.esp_screens_<navn>`** først (attributter `tiles`, `pages`, `columns`, `rows`).
  Roger redigerer også selv i editoren, så les på nytt rett før hver endring.
- Abonner på `esp_screens_tile_result` over WebSocket og vent på svar etter hver hendelse
  (`ok`, `slot`, `error`). Fyr én hendelse om gangen.
- Endre en flis = fjern den og legg den til på nytt.
- En flis med kontroll (`volume`, `brightness`, `setpoint` osv.) tegnes alltid **minst dobbelt bred**.
  `size: single` blir avvist hvis ruten ved siden av er opptatt.
- Navigasjonsflis: `entity: screen.page_<n>`. Den kan bare legges til når side `n` finnes.
- Klokke: `screen.clock` (`display: digital|analog|dial|flip`).
- Knapp som kjører en handling på flisens entitet: `action: media_player.media_next_track` (gir `tap: action`).
- Ren talltekst som temperaturflisene: `display: watch` på en `sensor`.
- Fullstendig felt- og kontrolliste: Tessera genererer sin egen agent-skill
  (`claude_skill.text()` i `/app/claude_skill.py`; i appen: Settings → Claude).

Minimalt eksempel (kjøres via rute 2, eller med `HASS_URL`/`HASS_TOKEN`):

```python
import asyncio, os, aiohttp
T = os.environ["SUPERVISOR_TOKEN"]; B = "http://supervisor/core/api/"
TILE = dict(screen="stue", page=3, row=4, column=1, size="3x1",
            entity="media_player.stue_arc_sonos", name="Neste sang",
            icon="skip-next", action="media_player.media_next_track")
async def main():
    h = {"Authorization": "Bearer " + T}
    async with aiohttp.ClientSession() as s, s.ws_connect("http://supervisor/core/websocket") as ws:
        await ws.receive_json(); await ws.send_json({"type": "auth", "access_token": T}); await ws.receive_json()
        await ws.send_json({"id": 1, "type": "subscribe_events", "event_type": "esp_screens_tile_result"}); await ws.receive_json()
        async with s.post(B + "events/esp_screens_add_tile", headers=h, json=TILE) as r: await r.read()
        while True:
            m = await asyncio.wait_for(ws.receive_json(), 10)
            if m.get("type") == "event": print(m["event"]["data"]); break
asyncio.run(main())
```

## Skjerminnstillinger (vanlige HA-entiteter på enheten)

`switch.<prefiks>dark_mode`, `select.<prefiks>rotation` (`0°`/`180°`; de gamle espcontrol-skjermene sto på 180°),
`number.<prefiks>standby_after` (s, min 60, steg 60), `number.<prefiks>normal_brightness`,
`number.<prefiks>standby_brightness`, `number.<prefiks>night_brightness`, `switch.<prefiks>night_mode`,
`time.<prefiks>night_starts/ends`, `button.<prefiks>wake` / `sleep`.

**Felle:** nattlysstyrke på 10 % ser helt svart ut på Guition 4″. Skjermspareren viste cover-bildet i ett
sekund og ble så «svart». Bruk minst 40 % (satt på begge skjermene).

Skjermspareren (f.eks. cover fra `media_player.stue_arc_sonos`) settes i Tessera-editoren og lagres i
`/data/screensavers.json`. Den starter når `standby_after` er nådd.

## Ny skjerm: fra espcontrol til Tessera uten USB

Fremgangsmåten som ble brukt 2026-11-19 på begge Guition-skjermene:

1. **Backup først, kun lesing:** `curl -s -N http://<ip>/events` i ca. 10 s gir alle tilstander fra
   espcontrol-webserveren (knapper `text/Button N Config`, `Button Order`, undermenyer, lysstyrke, rotasjon).
   Lagre som JSON hos Roger. Backupene ligger i `~/Downloads/espcontrol-*-2026-11-19.json` på Mac-en hans.
2. **Sjekk OTA uten passord:** ESPHome OTA-håndtrykk mot port 3232 (magic `6C 26 F7 5C 45`). Svaret `00 02`,
   `40`, `41` betyr ingen autentisering. espcontrol hadde ingen.
3. **Profil:** lag den i Tessera («New screen»), eller kopier en eksisterende profil med nytt navn.
   Lag **ny** API-nøkkel, nytt OTA-passord og nytt AP-passord, og skriv dem aldri ut.
4. **Bygg uten å flashe:** inne i containeren
   `ESPHOME_BUILD_PATH=/data/build/<navn> ESPHOME_DATA_DIR=/data/esphome ESPHOME_ESP_IDF_PREFIX=/data/idf PLATFORMIO_CORE_DIR=/data/platformio esphome compile <navn>.yaml`
   (cwd `/homeassistant/esphome`, ca. 10–15 min; start med `docker exec -d`).
5. **Flash bare etter Rogers ja** (Sov 2 krevde godkjenning fra sønnen hans):
   `esphome upload <navn>.yaml --device <ip>` med samme miljø. Det tar ca. 15 s.
   «Device rejected the handshake … retrying in plaintext» er normalt første gang.
6. HA-oppføringen fra espcontrol blir gjenbrukt (samme MAC), og Tessera kobler til skjermen av seg selv
   (loggen sier `<Navn>: live`).
7. Legg inn fliser med hendelsene over. Sett rotasjon, mørk modus, standby og nattlysstyrke.
   Flytt enheten til riktig HA-område (`config/device_registry/update` over WebSocket).
8. Oppdater kartet med `nettkart-publish` (IP, MAC, navn).

### Fra ESPMedia (jtenniswood/esphome-media-player) til Tessera, 10.1″ JC8012P4A1 (2026-11-21)

- Finn brettet: `curl http://<ip>/text_sensor/device_profile` på ESPMedia-skjermen.
- Velg Tessera-variant: ESPMedia bruker ESPHomes vanlige `mipi_dsi` + første LCD-tabell, som ikke starter på rev3-silisium,
  så brettet er **første utgave** (`packages/jc8012p4a1.yaml`). Gir bildet utvasket farge med en farget strek: bytt til
  `jc8012p4a1v2.yaml` via OTA. V3 trenger USB.
- ESPMedia har ikke OTA-passord og bruker HAs standard partisjonstabell, så `esphome upload <navn>.yaml --device <ip>` virker.
- HA beholder ESPMedia-oppføringen (samme MAC) og ber om reauth: fullfør flyten med `noise_psk` = ny API-nøkkel fra profilen
  (via REST `config/config_entries/flow/<id>`, uten å skrive ut nøkkelen). Enheten heter da «Stue 10».
- Tessera-sensoren `sensor.esp_screens_<navn>` dukker opp når første flis legges til.
- Skjermspareren lagres per HA-device-id i `/data/screensavers.json`; kopier Stue sin oppføring og restart appen.
- Kopi av Stue-oppsettet: les `sensor.esp_screens_stue`-flisene og send `esp_screens_add_tile` med samme
  `page/row/column/size`. En `action` kommer ut som `{"action": "..."}` i sensoren og må sendes som streng.
- Lysstyrke: standby og natt 40 % (lavere ser svart ut). Rotasjon kan bare være 0° eller 180°.
- Backup av ESPMedia-tilstanden: Mac `~/Downloads/espmedia-d395ce-backup-2026-11-21.txt`, pc6 `/root/espc-backup/`.

## Hjelpere laget for skjermene

- `sensor.arc_volum`: template-hjelper (UI) som viser volumet til `media_player.stue_arc_sonos` som 0–100,
  uten enhet. Brukes som `display: watch`-flis på Stue side 1.
- `script.arc_*` (9 stk, laget via `POST /api/config/script/config/<id>`): setter Stue Arc til volum 10 %
  og spiller en Sonos-favoritt (`media_content_type: favorite_item_id`, f.eks. `FV:2/61` = Daily Mix 1)
  eller en Spotify-spilleliste som delingslenke (`media_content_type: playlist`,
  `https://open.spotify.com/playlist/<id>`). Brukes som «run»-fliser på Stue side 6 (musikkside).
  Favoritt-ID-ene finnes med `media_player/browse_media` på `media_player.stue_arc_sonos` (type `favorites`).

- `script.spotify_volum_ned` / `script.spotify_volum_opp` (±5 %) og `sensor.spotify_volum` (template-hjelper, 0–100):
  Stue side 2 rad 5. Virker når Spotify spiller på en styrbar enhet (PC1 = «P1W»).
- Svart skjerm i standby: sjekk `number.<skjerm>_standby_brightness` (0 = svart) og at skjermspareren har
  `show: true` i `/data/screensavers.json`. Fila leses bare ved oppstart: endre den og restart appen
  (`POST http://supervisor/addons/self/restart` fra containeren). Stue: `more` = Spotify-entiteten, så cover vises
  også når Spotify spiller fra PC1 og Arc står på TV-kilden.

### Spotify-begrensninger (verifisert 2026-11-20)

- `media_player.101_stue_spotify_rogerlillefosse` har bare `SELECT_SOURCE` når avspilling skjer på Sonos
  eller via AirPlay: Spotify Web API regner Sonos som «restricted device». Bruk Sonos-entiteten til neste/volum.
- `script.neste_sang`: «Neste sang»-flisene (Stue side 1, 2, 5, 6) kjører dette scriptet. Har Spotify-entiteten
  `NEXT_TRACK` (bit 32) og spiller, hoppes det via Spotify (f.eks. Spotify-appen på PC1 under gaming); ellers
  sendes neste til `media_player.stue_arc_sonos`.
- Spotify DJ (start eller bytt sjanger) kan ikke styres via Web API, HA, iOS-snarveier eller Sonos.
  Daily Mix og andre Spotify-eide spillelister må lagres som Sonos-favoritter for å kunne spilles fra HA.

## Feilsøking

- Appens logg: `docker logs --since 10m app_ec8ae0ed_esp_screen_manager` (via `qm guest exec`).
- Skjermens logg: `esphome logs <navn>.yaml --device <ip>` inne i containeren (med `timeout 60`).
  Slå på `switch.<prefiks>debug_mode` midlertidig for mer detaljer, og slå den av etterpå.
- `Pressure: live tiles 1/2 …` i skjermloggen betyr at minnet er presset. Unngå mange tunge media-/cover-fliser.
- Rydd midlertidige filer i `/data` etter deg.
