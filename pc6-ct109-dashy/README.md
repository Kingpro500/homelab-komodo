# Dashy — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-dashy`
- **Address:** `http://10.0.0.128:3011`
- **Runtime config:** `/opt/dashy`

Dashy stores its config in `conf.yml` under `/opt/dashy` and is fully editable
from its own web UI. `conf.yml` is therefore runtime data and stays out of Git,
the same arrangement as Homepage. A starter `conf.yml` with every homelab
service is committed at `config/conf.yml` for reference; copy it to
`/opt/dashy/conf.yml` on CT109 if you want the dashboard populated on first
load instead of building it by hand in the UI.

Komodo variable: `DASHY_CONFIG_PATH=/opt/dashy`

The committed config uses the Dashy 4.7 format: `sections` with nested `items`,
and `appConfig` in place of the old top-level `settings` block. Dashy 4.7's
`ConfigSchema.json` sets `additionalProperties: false` at the root, so the
older `services`/`layout`/`settings` layout is rejected by `yarn validate-config`
and by the built-in JSON editor. It was verified against that schema.