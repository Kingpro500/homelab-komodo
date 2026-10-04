# tools

## check_homepage.py

Verifies that every service in `homepage/config/services.yaml` still points at a
guest (or node, router, or VM) that exists in Proxmox with the CT/VM number and
node recorded correctly.

A link drifts when a container is recreated, gets a new address, or moves to
another host. That happened here twice: Emby changed IP, and n8n moved from pc1
to pc6. Nothing broke, but the Homepage described systems that no longer
existed in that form.

```
python3 tools/check_homepage.py
```

Prints one line per mismatch and exits with `Avvik: N`. Zero means every entry
resolves.

Exit code is always 0, so it is safe to run from a schedule and parse the output
instead. It only reads Proxmox; it never changes anything.

Credentials come from `PROXMOX_URL`, `PROXMOX_TOKEN_ID` and
`PROXMOX_TOKEN_SECRET`, read from the environment or from the dotenv file at
`~/.hermes/.env`. Override the file with `HOMELAB_ENVFILE`.

## seed-heimdall.js

Mirrors `homepage/config/services.yaml` into Heimdall, grouped the same way.
Heimdall 2.8 keeps apps in SQLite, so there is no config file to commit and the
dashboard is seeded over its REST API instead.

```bash
SCRATCH=/path/to/repo-checkout node tools/seed-heimdall.js --dry-run
SCRATCH=/path/to/repo-checkout node tools/seed-heimdall.js
```

Idempotent: apps already present are skipped, so a re-run after adding services
to `services.yaml` only creates the new ones. Run `--dry-run` first to see how
many would be created and which icon each service ends up with.

Three things about this app that are not obvious from the docs:

- **POST needs a CSRF token.** The API routes sit behind Laravel's web
  middleware, so a bare POST returns `419 CSRF token mismatch` and creates
  nothing. Prime the session with `GET /`, then send the URL-decoded
  `XSRF-TOKEN` cookie back as `X-XSRF-TOKEN`.
- **Send `appdescription`, not `description`.** `storelogic()` overwrites
  `description` with a JSON config blob via `Item::checkConfig()`, so a plain
  string there is silently discarded and the tile shows no text.
- **Icons are fetched server-side through an SSRF guard** that rejects private
  addresses. A URL that cannot be fetched throws a validation error and aborts
  that create. Every candidate icon URL is probed first, and only the ones that
  answer are sent. Apps in Heimdall's own library (681 entries) send `appid`
  instead and use the bundled icon with no network call at all.

## heimdall-post-seed.php

Run inside the container after seeding:

```bash
pct exec 109 -- docker exec -i heimdall sh -c "cat > /tmp/descriptions.json" < descriptions.json
pct exec 109 -- docker exec -i heimdall php < tools/heimdall-post-seed.php
pct exec 109 -- docker restart heimdall
```

It does the two things the API cannot:

- **Pins the categories.** `resolveTags()` creates tags without `pinned`, and the
  `categories` branch of `ItemController::dash()` only lists items that have
  children *and* are themselves pinned. Skipping this leaves a populated database
  and an empty dashboard — the failure is silent and `GET /api/item` still
  returns every app.
- **Backfills `appdescription`** for items seeded with `description`.
  `PUT /api/item/{id}` is an empty stub in 2.8.3, so there is no API path for it.

Both steps are idempotent. `treat_tags_as` must also be `categories`; with the
default `folders` the dashboard only looks for apps parented to the root item.

Verify against the rendered page, not the API:

```bash
curl -s http://10.0.0.128:3012/ | grep -c 'no pinned applications'   # 0 means populated
```

`GET /api/item` returning 49 items proves nothing about whether the dashboard
shows them.
