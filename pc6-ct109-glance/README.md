# Glance — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-glance`
- **Address:** `http://10.0.0.128:3010`
- **Runtime config:** `/opt/glance`

Glance has no web UI for its configuration, so `glance.yml` is committed here in
Git as `config/glance.yml` and copied to `/opt/glance/glance.yml` on CT109 once.
Glance hot-reloads that file, so later edits can be made in Git and pushed.

Komodo variable: `GLANCE_CONFIG_PATH=/opt/glance`

`docker.sock` is mounted read-only for the `docker-containers` widget. Glance only
ever reads from it.