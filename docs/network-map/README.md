# Nettverkskart — Homelab 10.0.0.0/24

Interaktivt nettverkskart over hele homelab-et. Frittstående HTML (ingen eksterne
avhengigheter, fungerer offline) — åpne `nettverkskart.html` i en nettleser,
eller host den som en intern webside (se nedenfor).

## Data (sist generert 6. okt 2026)

Kartet bygges fra levende kilder, ikke fra et håndskrevet notat:

| Kilde | Hva |
|---|---|
| OPNsense `get_arp` | 48 enheter på LAN, med MAC + produsent |
| Proxmox API (`cluster/resources` + gjest-konfig) | 19 VM/CT med faktiske IP-er |
| Homepage `services.yaml` | tjenestebeholdningen |
| OPNsense config.xml / konfig-notat | switch-lag, WAN, portforward, DNS-kjede |

## Hvordan regenerere

```sh
ssh root@10.0.0.102   # eller en node i klusteret
# 1. Hent ARP fra OPNsense (les, skriv-token ikke nødvendig)
curl -sk -u "$OPNSENSE_API_KEY:$OPNSENSE_API_SECRET" \
  -X POST "$OPNSENSE_URL/api/diagnostics/interface/get_arp" -d '{}'
# 2. Hent gjesteliste med IP-konfig fra Proxmox
#    (scriptene ~/.hermes/scripts/proxmox_guests.py i CT157 dekker dette)
```

Kartet er en HTML-skisse; oppdater datafeltene og gjesteblokkene ved store
endringer. Vedlikeholdes av Hermes (CT157).

## Hvordan hoste som intern webside

Homelab-et kjører allerede en statisk webside-server kapabelt i CT109. Enkleste
vei (uten ny node):

1. **Nginx i CT109 den eksisterende dockeren** — legg en liten `nginx:alpine`
   container i `pc6-ct109-node`-stacken (eller en egen `pc6-ct109-web`-stack),
   mount denne mappa som `:/usr/share/nginx/html:ro`, publiser en port (f.eks.
   `10.0.0.128:3020`).
2. Eller **del gjennom FileBrowser** (allerede oppe på `10.0.0.150:8097`) — kopier
   mappa til `/media` og les HTML derfra.
3. Legg en tile i `homepage/config/services.yaml` pekende på den nye porten,
   slik at kartet er klikkbart fra dashbordet.

Siden gethomepage kun gir *status* (ikke start/stopp), bruk `dockctl`
(`10.0.0.128:3015`) for å få containeren opp hvis den ikke starter selv.

## Levende tjenestestatus + av/på-knapper (6. okt 2026)

Siden er statisk HTML men henter levende status fra `homelab-audit` på CT157
(`10.0.0.135:9118`), cross-origin med CORS aktivert server-side:

| Sti | Auth | Beskrivelse |
|---|---|---|
| `GET /status` | nei | `{"services":[{"name","host","port","up"}],...}` — TCP-prober parallelt, kun tjenestene i `servicemap_status.SERVICES` (bare dem vi bruker). |
| `POST /control` | ja (Bearer `AUDIT_TOKEN`) | Body `{"vmid":153,"action":"on\|off"}` — kjører `pct start/stop` på pc9 via SSH fra CT157. Tillatte vmider: 111,152,153,154,155. |

Kode på CT157 (`~/.hermes/scripts/`): `servicemap_status.py`,
`servicemap_control.py` (VMID-mapping), og rutene + CORS i
`homelab_audit_server.py`. Restart av service: `systemctl --user restart homelab-audit`.

Av/på-knappene i nettleseren krever `AUDIT_TOKEN` i `localStorage`:

```js
localStorage.setItem("homelab_audit_token", "<AUDIT_TOKEN fra ~/.hermes/.env>")
```

**iVentoy (111), Immich (153), Paperless (154), UniFi (155) på pc9 er bevisst
stoppet** for å spare ressurser — de brukes ikke for tiden. Det er
normaltilstanden; status-siden viser dem røde. Start dem via av/på-knappen
eller `pct start <vmid>` når du trenger dem.
