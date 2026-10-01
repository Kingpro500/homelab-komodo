# Speedtest Tracker — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-speedtest-tracker`
- **Address:** `http://10.0.0.128:8765`
- **Runtime config/database:** `/opt/speedtest-tracker`

The former Tower configuration includes the SQLite database and is copied once
as runtime data. Keep the Tower source as rollback. Required Komodo variables:

- `SPEEDTEST_CONFIG_PATH=/opt/speedtest-tracker`
- `SPEEDTEST_APP_KEY` (secret; reuse the existing application key)
