# Crafty Controller — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-crafty`
- **Address:** `http://10.0.0.128:8000`

Crafty Controller is a panel for running Minecraft (and other game) servers. The
panel itself is light; the Java servers it launches are not, which is why
`mem_limit` is set to 2 GB — a single Minecraft server wants 1–2 GB and Crafty
reports what is left when you add one through the UI.

Image is `lscr.io/linuxserver/cygot-docker`, the LinuxServer packaging of
Crafty. It was chosen over the upstream `mholt/crafty-controller` image because it
follows the same PUID/PGID/TZ convention as the other stacks on this node
(`pc6-ct109-speedtest-tracker`), and is maintained independently of upstream.

State lives in the named volume `crafty-data`, which Docker creates on first
deploy — nothing needs preparing on the host. That one volume holds both the
Crafty configuration and any server files added later through the UI, so a
`docker compose down` will not lose them but a volume prune would.

First run creates an admin account; the credentials are chosen in the browser, so
there is nothing to put in Stack Environment and no secrets in the repo.