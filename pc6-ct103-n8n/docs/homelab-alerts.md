# Homelab-ressurs-alarmer (webhook `homelab-alerts`)

- **n8n-ID:** `kALMQJZ2VgJLSOHp` · **Trigger:** POST `http://10.0.0.119:5678/webhook/homelab-alerts`
- **Kilder:** NetAlertX (CT126), Alertmanager/Grafana, `blaff-logger`, drift- og versjonsvakt.
- **Eksport:** [workflows/homelab-alerts.json](../workflows/homelab-alerts.json)

## Flyt
1. **Webhook** → to grener:
   - **Logg hendelse** → POST `/webhook/events` (alle hendelser logges alltid).
   - **Stilleperiode og global timegrense** → **Send til telefon** (POST `10.0.0.135:9118/notify`).
2. Stilleperiode: ingen push 23:00–06:00 (Europe/Oslo); aldri etterlevert.
3. Grenser (workflow static data):
   - «New Device» / «ny enhet» (regex på body): egen grense, **1 push per 10 min** (`last_newdevice_push_at`).
   - Alt annet: global grense, **1 push per 60 min** (`last_phone_push_at`).

## Endringslogg
- 2026-11-11: egen grense for nye enheter (tidligere stoppet den globale timegrensen 8 «New Device»-varsler samme dag). Backup før endring tatt. Hermes, godkjent av Roger.

Ingen hemmeligheter i eksporten (kontrollert).
