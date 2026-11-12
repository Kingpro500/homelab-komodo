# Media playback performance watch

Read-only overvåking av faktisk Emby-avspillingshelse via eksisterende n8n- og
homelab-audit-kjede. Workflowen kjører hvert andre minutt og bruker eksisterende
`POST /media/check` med n8n-credentialen `Homelab Audit Header`.

## Måler

- Emby-/medietjenestehelse gjennom eksisterende dype medieprobe.
- Nylige FFmpeg-transcode-logger på CT 200.
- Kildesti for hver lesbare transcodejobb.
- Siste `speed=`-verdi.
- Siste `ThrottleBuffer` når den finnes.
- Antall lesbare transcodejobber og lesefeil.

## Varslingspolicy

- `speed < 1.0x` er playback-risiko.
- `speed < 1.15x` er marginvarsel, men varsler ikke alene.
- Risiko må forekomme i to påfølgende prøver med samme fingerprint.
- Varsling dedupliseres med workflow static data og maksimalt én gang per time
  per vedvarende hendelse.
- Varsling går gjennom eksisterende `POST /notify` og telefonbanen.
- Workflowen er read-only: den stopper FFmpeg, sletter transcode-cache og
  restarter ikke Emby eller CT 200 aldri.

## Implementasjon

Adapteren `scripts/media_performance_adapter.py` leser kun de siste transcode-
loggene via den eksisterende tvungne SSH-adapteren. `media_recovery_adapter.py`
legger playback-snapshoten inn i svaret fra den eksisterende `/media/check`-banen.
Ingen credential-verdi ligger i repoet.

## Test og aktivering

Kjør først lokale parser-/syntax-tester og importer workflowen i n8n som
inaktiv. Les tilbake live workflow-grafen, kjør en ekte execution og kontroller
at `playback_performance.jobs` inneholder `path`, `speed` og eventuell
`throttle_buffer_s`. Aktiver først når disse feltene er verifisert i en ekte
execution. Ingen recovery-gren skal legges til uten separat beslutning og tester.
