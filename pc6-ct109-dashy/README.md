# Dashy — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-dashy`
- **Address:** `http://10.0.0.128:3011`

Config lives in the named volume `dashy-data`, which Docker creates on first
deploy. Nothing needs preparing on the host.

Dashy stores its config in `conf.yml` inside that volume and is fully editable
from its own web UI, so the runtime file is deliberately not in Git. A starter
`conf.yml` with every homelab service is committed at `config/conf.yml` for
reference; paste its contents into Dashy's config editor, or add services by
hand in the UI.

The committed config uses the Dashy 4.7 format: `sections` with nested `items`,
and `appConfig` in place of the old top-level `settings` block. Dashy 4.7's
`ConfigSchema.json` sets `additionalProperties: false` at the root, so the older
`services`/`layout`/`settings` layout is rejected by `yarn validate-config` and by
the built-in JSON editor. It was verified against that schema.