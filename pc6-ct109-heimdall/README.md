# Heimdall — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-heimdall`
- **Address:** `http://10.0.0.128:3012`

Config lives in the named volume `heimdall-data`, which Docker creates on first
deploy. Nothing needs preparing on the host.

Heimdall 2.8.x keeps apps in a SQLite database (`app.sqlite`) inside the volume,
not in a JSON file, so there is no config to commit. Everything is added through
the web UI or imported from a backup file (Settings > Import).

`ALLOW_INTERNAL_REQUESTS=true` is required: without it Heimdall refuses to
resolve or fetch any RFC1918 address, which is every service on this network.