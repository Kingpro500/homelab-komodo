# pc6-ct109-web — intern nettverkskart (nginx)

Intern statisk webside som serverer `docs/network-map/` (nettverkskartet) på
`http://10.0.0.128:3020/`. Deployes via Komodo på `pc6-ct109-node`.

## Hva dette er

- `nginx:alpine` — et par MB, ingen eksterne avhengigheter.
- Serverer nettverkskartet (`nettverkskart.html`) som index på rot-URL-en.
- **LAN-alene:** ingen WAN-portforward. Når kun internt.
- Knyttes til Homepage-dashbordet via tilen «Nettverkskart» i `services.yaml`
  (peker på `10.0.0.128:3020`).

## Repo-layout (viktig for mount)

`git pull` kloner hele repoet til `/opt/komodo/stacks/pc6-ct109-web/`. Denne
compose-fila ligger i `run_directory` `pc6-ct109-web`, så:

- `../docs/network-map` → repoets `docs/network-map` (webroot, read-only)
- `./default.conf` → repoets `pc6-ct109-web/default.conf` (nginx-konfig)

Vil du legge til flere statiske sider: slipp HTML-en i `docs/network-map/`.

## Vedlikehold

Regenerér kartet (data fra OPNsense ARP + Proxmox) og forny `.html`-en i
`docs/network-map/`. nginx serverer filene live fra mount-en; en redeploy
kreves bare når hele stacken endres.
