# Nettverkskart — Homelab 10.0.0.0/24

Frittstående startside (HTML) over hele homelab-et. Åpne `nettverkskart.html`
eller se den live på **http://10.0.0.128:3020/** (nginx i `pc6-ct109-web`).

## ⛔ PÅLAGT: NODE-SAMMENDRAGET + VERSJONERING — MÅ IKKE FJERNES

**Det finnes ETT element som er beskyttet uten unntak:** node-sammendraget —
de fire maskinene (pc1 · Gaming, pc6 · Tower, pc9 · Minipc, pc8 · pve) med
**CPU, RAM og Disk** øverst i «📋 Serviceoversikt». Det er `#node-resources` i
`nettverkskart.html` og fylles live fra `GET http://10.0.0.135:9118/nodes`.

- Det ble **fjernet én gang** (commit `acac5cc`, «gjenopprett statisk oversikt»)
  og er siden gjenopprettet. **Gjenopplever du å se det forsvunnet, gjenopprett
  det umiddelbart fra `/nodes` — ikke «rydd» det bort.**
- **Du må ALDRI**: fjerne `#node-resources`, `.nr-card`-CSS-en, `renderNodes()`,
  eller erstatte innholdet med noe annet. Du kan legge til elementer i tillegg.
- Kommentaren i HTML-en rett over `#node-resources` er også der av denne grunn.

**Versjonering:** Skjema = **`baseversjon.desimal`**. Vi ligger på base `2`; hver
minste endring hever sub-versjonen med 0.001 (`2.001`, `2.002`, …); ved store
omskrivinger hopper vi til neste baseversjon (`3`, …). Arkiver forrige versjon
til `versions/vNN/` og oppdater `versions/index.html`. Topp-høyre på siden viser
versjonsnummeret, og `versions/` er indeksen med klikkbare gamle versjoner. Aldri
slett gamle versjoner.

## ⚠️ Vedlikeholdsregler — LES FØR DU ENDRER

## Data (sist generert 8. okt 2026)

Dette dokumentet har blitt ødelagt flere ganger av AI-er som har:
- flyttet gjester til feil node og påstått ting som ikke stemmer;
- erstattet den pålitelige statiske oversikten med én stor JS-tabell som
  faller ut når et endepunkt er nede;
- markert reelle tjenester som «finnes ikke» eller omvendt.

Vær derfor nøye med dette:

1. **Sjekk levende data FØR du skriver noe.** Kilden er sannheten, ikke det som
   står i fila:
   - Gjester + IP + hvilken node: Proxmox
     `GET /api2/json/cluster/resources?type=vm` + gjestens `config`
     (token-en i `~/.hermes/.env` på CT157).
   - CPU-modell: `GET /api2/json/nodes/<node>/status` -> `cpuinfo.model`.
   - Kjører/stoppet: `info.status` = `running`/`stopped`. For containere,
     bekreft med `docker ps` i CT-en via `pct exec`.
2. **Behold den statiske service-oversikten og datamaskin-oversikten.** De er
   hovedinnholdet. Du kan legge til ekstra, men ikke fjerne dem.
3. **En stoppet gjest betyr ikke at den ikke finnes.** Mange CT-er er stoppet
   med vilje (arkiverte legacy fra Unraid/Tower, eller sparing). Ikke slett dem.
4. **Når du legger til en enhet:** legg den i den statiske tabellen (riktig
   node), i nettverkskart-seksjonen og eventuelt IoT-lista — med IP og node
   hentet fra Proxmox/ARP.
5. **Forklar avvik** (motsier Proxmox/ARP) i kommentarfeltet nederst i fila i
   stedet for bare å «fikse» uten kilde.

## Nåværende gjestetilstand (verifisert 6. okt 2026)

| Node | kjører | stoppet/arkivert |
|---|---|---|
| pve (pc8) N150 | VM100 HA, CT102 Komodo/NetBox/step-CA, CT115 pihole, CT110 periphery | — |
| pc6 N355 | VM101 Unraid, CT103 n8n/OWU/gjeld, CT109 *arr/dash/nettkart/udleje, CT151 emby, CT157 hermes | CT104, CT107 mediespillere, CT108 legacy, CT159 abs-ngrok, CT160 lancache |
| pc9 N100 | CT106 tunarr, CT116 pihole, CT152 roon, CT155 uniFi | CT111 iventoy, CT153 immich, CT154 paperless |
| pc1 3900X | — | CT105 mediespiller, CT156 ollama, CT158 browsers |

**Merk:** ct107/108/159/160 er arkiverte legacy-CT-er fra Unraid/Tower, stoppet
med vilje. De kommer opp ved behov — slett dem ikke.

## CPU-er (live fra Proxmox /nodes/*/status)

- pc7 (OPNsense) = N150, pc8 (pve) = N150, pc9 = N100, pc6 = **Core 3 N355**,
  pc1 = Ryzen 9 3900X, pc3 = Apple M1, pc4 = Ryzen 7 5800X; pc2/pc10 inaktive.

## Verdier å ikke lure seg på

- Sonos: ARP viser 7; de to Sonos One (Arc-surround) er lagt inn som offline.
- ESP: 5 i ARP. EspMedia 10.1″ = **10.0.0.48**, EspControl lys = .8, media = .86.
- Portforwards: Emby 8096 → 10.0.0.150 (aktiv), Valheim UDP 2456-58 (lukket).
- DNS-kjede: klient → Pi-hole (.115/.116) → Unbound (10.0.0.1) → internett.

## Hvordan regenerere

```sh
ssh root@10.0.0.120   # pc6, eller en node i klusteret
# 1. ARP fra OPNsense (les)
curl -sk -u "$OPNSENSE_API_KEY:$OPNSENSE_API_SECRET" \
  -X POST "$OPNSENSE_URL/api/diagnostics/interface/get_arp" -d '{}'
# 2. Gjester + IP: Proxmox cluster/resources + gjeste-config
#    (~/.hermes/scripts/proxmox_guests.py i CT157)
```

## Hvordan hoste som intern webside

nginx i `pc6-ct109-web`-stacken serverer `docs/network-map/` read-only på
`10.0.0.128:3020`. Etter endring: commit + push, og `git pull`/`git reset --hard
origin/main` i `/opt/komodo/stacks/pc6-ct109-web` på pc6 (CT109 kjøres via
`pct exec 109 -- sh <script>`). Tile «Nettverkskart» i Homepage peker hit.

## Levende tjenestestatus + av/på-knapper (6. okt 2026)

Siden er statisk HTML men henter levende status fra `homelab-audit` på CT157
(`10.0.0.135:9118`), cross-origin med CORS server-side:

| Sti | Auth | Beskrivelse |
|---|---|---|
| `GET /status` | nei | `{"services":[{"name","host","port","up"}],...}` — TCP-prober parallelt. |
| `POST /control` | ja (Bearer `AUDIT_TOKEN`) | `{"vmid":153,"action":"on\|off"}` — `pct start/stop`. Tillatte vmider: 111,152,153,154,155. |
| `GET /nodes` | nei | gjester per node (brukes for ressurskort/tabell). |

Kode på CT157 (`~/.hermes/scripts/`): `servicemap_status.py`,
`servicemap_control.py` (VMID-mapping), rutene + CORS i
`homelab_audit_server.py`. Restart: `systemctl --user restart homelab-audit`.

Av/på-knappene krever `AUDIT_TOKEN`:
```js
localStorage.setItem("homelab_audit_token", "<AUDIT_TOKEN fra ~/.hermes/.env>")
```