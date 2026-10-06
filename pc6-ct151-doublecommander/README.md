# Double Commander on CT 151 (emby-pc6)

Modern twin-pane file manager over the Unraid media NFS share, in the browser
(KasmVNC). See `docker-compose.yml` header for full setup notes. Runs on the
same privileged container as Emby as PUID 99 / PGID 100, so moved files keep
the media share's owner. Chosen as the modern alternative to the Krusader
stack (same side-by-side panels, actively maintained, lighter than a full KDE
desktop).

## Deploy (Komodo)

- Server: `emby-pc6` (stack `pc6-ct151-doublecommander`)
- Repo: `Kingpro500/homelab-komodo`, branch `main`, run-directory `pc6-ct151-doublecommander`
- Stack variables (optional): see `.env.example`

Prepare config dir once on CT 151 (`/opt/doublecommander`, owner 99:100), then
deploy.

## Access

```
http://10.0.0.150:8099
```

Reach the desktop, open Double Commander; container mounts `/media` (the Unraid
media share).

## Scope note

Like FileBrowser and Krusader, currently only the `media` share (the sole Unraid
share NFS-bound into CT 151). To also manage `downloads`/`documents`, those must
be NFS-exported from Unraid and bound into CT 151 + one short Emby-CT restart.
