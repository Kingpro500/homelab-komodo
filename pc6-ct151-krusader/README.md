# Krusader on CT 151 (emby-pc6)

KDE twin-pane file manager over the Unraid media NFS share, in the browser.
See `docker-compose.yml` header for the full setup notes. Runs on the same
privileged container as Emby; Unraid NFS `root_squash` maps the container's
root to uid 99, so moved/created files keep the media share's owner.

Chose **`jlesage/krusader`** over the `binhex/arch-krusader` you likely ran on
Unraid before (a KDE-in-browser container broke here previously) because
jlesage is the most reliable GUI-in-browser base. If you specifically want the
binhex one, it is a one-line image change.

## Deploy (Komodo)

- Server: `emby-pc6` (stack `pc6-ct151-krusader`)
- Repo: `Kingpro500/homelab-komodo`, branch `main`, run-directory `pc6-ct151-krusader`
- Stack variables (optional): see `.env.example`

Prepare config dir once on CT 151 (`/opt/krusader`), then deploy.

## Access

```
http://10.0.0.150:8098
```

Web UI is jlesage noVNC. Reach KDE, open Krusader from the app menu. The
container mounts `/media` (the Unraid media share).

## Scope note

Like FileBrowser, Krusader currently reaches only the `media` share (the sole
Unraid share NFS-bound into CT 151). To also manage `downloads`/`documents`,
those must be NFS-exported from Unraid and bound into CT 151 (`mpX` in
`/etc/pve/lxc/151.conf` + one short Emby-CT restart).
