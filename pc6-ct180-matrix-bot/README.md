# CT180 Matrix AI-bot

Dette er den versjonskontrollerte kilden til `hermes-ai-matrix.service` i CT180.

## Deploy

Deploy skal utføres manuelt fra administrasjonsmaskinen etter gjennomgang av diff og syntakssjekk. Tokens skal aldri kopieres til repositoriet.

```bash
python3 -m py_compile pc6-ct180-matrix-bot/hermes_ai_matrix.py
# Kopier filen til CT180 som /opt/synapse/hermes_ai_matrix.py
# Verifiser deretter tjenesten og journalen med begrenset sudo-tilgang.
```

## Sikkerhet

- Matrix- og Home Assistant-tokens leses kun fra filer på CT180.
- Kun `media_player.stue_arc_sonos` og `light.stue` kan styres.
- Botten bruker faste Home Assistant-kall; den lokale modellen får ingen verktøykall.
- Talegjenkjenning er ikke aktivert.
- Ingen PC1-start, restart eller strømstyring er implementert.
