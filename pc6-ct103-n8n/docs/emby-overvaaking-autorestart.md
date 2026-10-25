# Emby-overvåking og autorestart

Workflowen er deaktivert inntil ende-til-ende-test er godkjent.

## Sikkerhetsgater

- Første feil gir ingen recovery.
- Andre identiske feil kreves.
- `active_sessions_known` må være `true`.
- `active_streams` må være `0`.
- Maintenance lock blokkerer recovery.
- Maksimalt ett restartforsøk per 24 timer.
- 30 minutters cooldown mellom forsøk.
- Samme feilfingerprint dedupliseres i n8n static data.
- Ukjent sessions-status rapporteres som `sessions_unknown`.

## Verifisering

Recovery-gaten er testet lokalt med første feil, andre feil, aktiv stream, ukjent sessions-status og maintenance lock. JavaScript er validert med `node --check`.

## Produksjonsstatus

Workflow-ID: `dK3dJJIQ7smvUy9v`\n
Aktiv: `false`

Ingen automatisk Emby-restart skal aktiveres før runtime-test av alle feilbaner er utført.
