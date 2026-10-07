# Legacy-dockere — pc6 CT108 (flyttet fra Unraid)

- **CT / node:** CT108 på pc6 (10.0.0.120)
- **LXC:** `pc6-ct108-legacy-dockere-gammel`
- **IP:** `10.0.0.161`
- **Runtime-data:** `/opt/legacy-dockers/appdata` (i CT-en)
- **Status:** **stoppet, `onboot: 0` (autostart av)** — midlertidig, opprydding pågår

## Tjenester (flyttet fra Unraid-Tower)

Appdata-mapper bekreftet under `/opt/legacy-dockers/appdata`:

| App | Rolle |
|---|---|
| iPXE-buildweb | bygge iPXE-menu/firmware over nett |
| netbootxyz | nettinstall/USB-boot-verktøy |
| openvscode-server | VS Code i nettleser |
| Flame | applanser / diverse-dashbord |
| 4get | meta-søkemotor-proxy |
| Linkding | bokmerker |
| unraid-simple-monitoring-api | JSON-status-API for Unraid |
| cloudflared | Cloudflare Tunnel (ekstern tilgang) |
| valheim | Valheim (spill) — **kun data** her |

## Bakgrunn

Alle kjørte tidligere som Docker-containere i Unraid-VM-en (`10.0.0.101`).
Unraid-Docker er skrudd av, så de er pakket ut i en egen CT på pc6.
Docker-ne er manuelle (ingen compose-filer) — start dem eksplisitt
(`docker start <navn>`) eller legg til en compose om de blir kandidater
for fast drift. Ngrok hadde ingen appdata å flytte og er ikke gjenopprettet.

Se BÅDE CT107 (media) og CT108 (dette) som midlertidige oppryddings-CT-er:
autostart er av, og de skal inn i Komodo/Homepage permanent først når
tjenestene avgjøres å ha verdi videre.

## Start

```sh
pct start 108          # på pc6
# deretter docker-start inni: pct exec 108 -- docker start <navn>
```