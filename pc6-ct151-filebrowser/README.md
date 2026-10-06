# FileBrowser on CT 151 (emby-pc6)

Web file manager so files can be moved between Unraid shares from a browser.
Runs on the same **privileged** container as Emby so it can write to the
Tower **media** NFS share (`/media` in CT 151, bound via `mp0`) without
breaking file ownership. The container runs as uid **99** (Unraid `nobody`) /
gid **100** (`users`), which passes straight through NFS `sec=sys` because the
container is privileged (an unprivileged CT would map these UIDs wrong and
writes would create files with the wrong owner).

This keeps Docker **off the Unraid VM**: the media files stay on Tower, but the
file manager that edits them lives on pc6.

## Deploy

Create this stack in Komodo on the **emby-pc6** server (server =
`pc6-ct151-emby`). For the stack action use **pull latest** and the repo path
`pc6-ct151-filebrowser` from `Kingpro500/homelab-komodo`.

Stack variables (all optional — defaults below are fine):

```dotenv
FILEBROWSER_MEDIA_PATH=/media
FILEBROWSER_CONFIG_PATH=/opt/filebrowser
TZ=Europe/Oslo
```

Before the first deployment, prepare the config dir on CT 151:

```bash
install -d -o 99 -g 100 -m 0755 /opt/filebrowser
```

(This is already done.)

## Access

Web UI is published on port **8097** of CT 151:

```
http://10.0.0.150:8097
```

First login asks you to create an admin account (the image ships standard
`admin`/`admin`, which it forces you to change). Root of the file view is
`/srv`, which maps to `/media` → the full Unraid `media` share.

## Scope note

FileBrowser can currently reach **only the `media` share** — that is the only
Unraid share NFS-bound into CT 151 (`mp0`). To also manage `downloads` /
`documents`, those shares must be NFS-exported from Unraid (share → NFS
Security → Export) and bound into CT 151 (`/etc/pve/lxc/151.conf` + one short
restart of the Emby CT). Deliberately left out for now (media-only per user
decision).
