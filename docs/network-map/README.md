# Nettverkskart — Homelab 10.0.0.0/24

Interaktivt nettverkskart over hele homelab-et. Frittstående HTML (ingen eksterne
avhengigheter, fungerer offline) — åpne `nettverkskart.html` i en nettleser,
eller host den som en intern webside (se nedenfor).

## Data (sist generert 8. okt 2026)

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
