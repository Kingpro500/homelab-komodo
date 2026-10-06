# Udlejning — formidlingsportal (MVP)

Formidlingsportal for udlejning af huse og lejligheder i Danmark. Vi ejer
ikke boligerne selv — udlejere lægger deres boliger ind, admin godkender,
og interesserede lejere sender en henvendelse.

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-udleje`
- **Address:** `http://10.0.0.128:3030`
- **Stack:** Flask + SQLAlchemy + PostgreSQL + gunicorn (Docker Compose)
- **Roller:** `udlejer` (lægger boliger ind) / `admin` (godkender, styrer brugere)

## Funktioner (MVP)

| Område | Hvad |
|---|---|
| Offentligt | Søg/filtrér på kommune, type, max. husleje, min. værelser; sortering |
| Offentligt | Objektkort med billede, pris, areal, værelser |
| Offentligt | Detaljeside med galleri, beskrivelse, økonomi-fakta, Leaflet-kort, henvendelsesformular |
| Udlejer-portal | Opret/rediger/slet boliger, upload billeder (jpg/png/webp), se henvendelser |
| Admin | Godkend/afvis/arkiver boliger, aktiver/deaktiver brugere |
| GDPR | Om/vilkår-side med GDPR-beskrivelse, ingen trackere |

## Arkitektur

- `app/models.py` — domænemodel: `User`, `Bolig`, `Billede`, `Henvendelse`
- `app/__init__.py` — app-fabrik, ruter, auth (CSRF + session), bildeopplastning
- `app/templates/` — Jinja-maler (dansk UI)
- `wsgi.py` — gunicorn-entrypunkt
- `Dockerfile` — `flask init-db` ved start, derefter gunicorn

## Sikkerhed

- Adgangskoder hashed med werkzeug (`generate_password_hash`)
- CSRF-token på alle POST-formularer (session-baseret)
- Session-cookie: HttpOnly + SameSite=Lax (Flask-defaults) med `SECRET_KEY` fra Komodo
- Rollebeskyttelse per route (`login_påkrævet`, `admin_påkrævet`)
- Uploads valideret til jpg/png/webp, `secure_filename`, egen upload-folder udenfor webroot
- Offentligt netværk: kun LAN-port på CT109, ingen WAN-port-forward

## Opsætning (Komodo Stack Environment)

| Variabel | Beskrivelse |
|---|---|
| `UDLEJE_DB_PASSWORD` | Postgres-adgangskode |
| `UDLEJE_SECRET_KEY` | Flask-sessionnøgle |
| `UDLEJE_ADMIN_EMAIL` | Første admin (oprettes ved init-db) |
| `UDLEJE_ADMIN_PASSWORD` | Første admin-adgangskode |
| `UDLEJE_POSTGRES_PATH` | Volume for Postgres-data (host-sti) |
| `UDLEJE_DATA_PATH` | Volume for uploads (host-sti) |

Eksempel-stier (tilpass din server): `/opt/komodo/stacks/pc6-ct109-udleje/data/{postgres,uploads}`

## Status: MVP

Dette er MVP v1. Kendte begrænsninger: ingen e-mail-udsendelse ved nye
henvendelser (skal bygges), ingen geokodning (udlejer angiver koordinater
manuelt), ingen betalings- eller fakturaflow, ingen billed-beskæring/
komprimering. Se `docs/` i repoet for den fulde plan.
