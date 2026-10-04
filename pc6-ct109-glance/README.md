# Glance — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-glance`
- **Address:** `http://10.0.0.128:3010`

Glance has no web UI for its configuration, so `glance.yml` lives in Git at the
stack root and is bind-mounted read-only:

```yaml
volumes:
  - ./glance.yml:/app/config/glance.yml:ro
```

The stack's `file_paths` is `docker-compose.yml` only. **`file_paths` is for extra
compose files** (Komodo runs `docker compose -f <each> ... config`), so putting
`glance.yml` in it makes Komodo try to parse Glance's YAML as a compose file and
the deploy fails with `additional properties 'pages', 'server', ... not allowed`.

No host preparation is needed at all: Komodo clones the whole repo to
`$root_directory/stacks/<stack>/`, and `run_directory` is `pc6-ct109-glance`, so
the relative path resolves inside the clone. Verified that Glance v0.8.6 starts
and serves with a read-only config file.

`docker.sock` is mounted read-only for the `docker-containers` widget. Glance only
ever reads from it.