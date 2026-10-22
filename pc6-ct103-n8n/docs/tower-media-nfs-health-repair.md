# Tower media NFS health and repair

**Workflow:** `Tower media NFS health and repair`

**Interval:** hvert femte minutt
**Formål:** oppdage en faktisk utilgjengelig NFS-/bind-mount, ikke bare at en
mount ser montert ut.

## Sikkerhetspolicy

Emby er prioritet én. Automatikk skal derfor aldri stoppe, restarte eller
remounte under Emby CT200. Dette er en bevisst endring etter at den gamle
CT151-logikken ble foreldet under renummereringen.

n8n bruker en låst SSH-nøkkel. På begge Proxmox-nodene kan nøkkelen bare kjøre
`/usr/local/sbin/n8n-tower-media-repair`; den kan ikke åpne shell, forwarde
porter eller velge andre kommandoer.

## Runtime-skript

| Node | Skriptet kontrollerer | Automatisk handling | Bevisst ikke automatisk |
|---|---|---|---|
| PC6 `10.0.0.120` | `/mnt/pve/Tower-media`, CT250 `/media`, CT210 `/scan/media` | Restarter CT250 og/eller CT210 ved stale bind mount når hostmounten er frisk | CT200/Emby, også ved hostmount-feil |
| PC9 `10.0.0.103` | seks mapper under CT106 `/media/*` | Restarter CT106/Tunarr ved stale bind mount når hostmounten er frisk | Host-remount som kan påvirke Roon CT220 |

Hostmount-feil returnerer exit `2`. n8n sender da kritisk iPhone-varsel i stedet
for å prøve en risikabel remount. Det gir en kontrollert vedlikeholdsoppgave
heller enn at automatikk gjør Emby eller Roon mer utilgjengelig.

En frisk kontroll skriver bare `tower-media: healthy`; dette gir ikke varsling.
`flock` hindrer overlappende reparasjoner.

## Varsling

Workflowen varsler iPhone via Home Assistant ved reparasjon eller feil. Uptime
Kuma overvåker i tillegg Tunarrs reelle M3U-feeder. Det dekker to ulike feil:

- NFS-/bind-mount-feil oppdages av n8n på filsystemnivå.
- Tunarr-feil som gjør Emby-feed ulesbar oppdages av Uptime Kuma.

## Gjenoppretting

Kildeskriptene er versjonert som:

- `scripts/n8n-tower-media-repair-pc6`
- `scripts/n8n-tower-media-repair-pc9`

Før skript byttes på en node skal den eksisterende `/usr/local/sbin`-filen
kopieres tidsstemplet, og den nye filen skal valideres med `bash -n`. Test kun
en frisk kontroll først. Ikke simuler stale mount på Emby.
