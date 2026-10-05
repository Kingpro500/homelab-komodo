# Crafty Controller — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-crafty`
- **Address:** `https://10.0.0.128:8000` — **self-signed certificate**, so the browser warns once.

Crafty Controller is a panel for running Minecraft and other game servers. The
panel is light; the Java servers it launches are not, hence `mem_limit: 2g`. Crafty
reports remaining headroom when you add a server through the UI.

State lives in the named volume `crafty-data` mounted at `/home/crafty`, which
Docker creates on first deploy — nothing needs preparing on the host.

## Which image, and why not the obvious one

Two commonly cited images do not work:

- `lscr.io/linuxserver/cygot-docker` — does not exist. LinuxServer's own
  catalogue has no cygot entry, and `docker pull` is denied.
- `mholt/crafty-controller` — the upstream image, gone from Docker Hub. Also denied.

`cybercube/crafty-controller` is the remaining maintained fork. Verified by
pulling it and inspecting the image, not from its docs: it is Crafty v3.2, runs as
the `crafty` user, and keeps its configuration under that user's home.

## tty and stdin_open are load-bearing

Crafty's entrypoint is `sh -c "python3 crafty.py"`. Without a TTY the shell
wrapper reads EOF on Crafty's interactive prompt and exits 0. Under
`restart: unless-stopped` that is a crash loop, and it looks like a broken image
rather than a mis-deployed one. With `tty: true` and `stdin_open: true` the
container stays up and answers HTTP 200. Verified both ways.

## First run

Crafty generates an admin account and prints it in the container log:

```bash
pct exec 109 -- docker logs crafty | grep -E 'Username|Password'
```

Open `https://10.0.0.128:8000`, accept the certificate warning, and log in.