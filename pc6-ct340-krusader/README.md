# Krusader on its own CT (pc6-ct161-krusader)

KDE twin-pane file manager over the Unraid media NFS, in the browser.
Dedicated privileged CT on pc6 so it can be **started/stopped on demand** from
Proxmox — CT start = Krusader up, CT stop = Krusader down. See
`docker-compose.yml` for the full setup and deploy/debug commands.

- **Web UI:** `http://10.0.0.142:8098`
- **Scope:** serves the `media` share (bound into the CT as `/media` via mp0).
  For `downloads`/`documents` too, those must be NFS-exported from Unraid and
  bound into CT 161 (add `mp1`/`mp2` in `/etc/pve/lxc/161.conf` + one restart).

Chosen over FileBrowser/Double Commander (both removed): Krusader's jlesage
base is stable over plain HTTP, and a dedicated, start/stop-able CT is the
cleanest fit for this use.
