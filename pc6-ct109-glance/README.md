# Glance — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-glance`
- **Address:** `http://10.0.0.128:3010`

Glance has no web UI for its configuration, so `glance.yml` lives in Git at the
stack root and is deployed with the stack. The stack's `file_paths` lists it
alongside the compose file:

```
docker-compose.yml
glance.yml
```

The compose file bind-mounts `./glance.yml` read-only, relative to the cloned
repo, so nothing has to be prepared on the host by hand. Verified that Glance
v0.8.6 starts and serves with a read-only config file.

`glance.yml` deliberately sits at the stack root rather than in a `config/`
subdirectory: a first attempt with `file_paths: [docker-compose.yml,
config/glance.yml]` failed to deploy while every other stack in this Komodo lists
a single file, so the simpler shape is the one known to work here.

`docker.sock` is mounted read-only for the `docker-containers` widget. Glance only
ever reads from it.