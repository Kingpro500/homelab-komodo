# Tower media NFS health and repair

**Workflow-id:** `tower-media-nfs-health-repair`
**Eksport:** `workflows/tower-media-nfs-health-repair.json`
**Status:** aktiv (hvert 5. min)

## Hva den overvåker og hvorfor

NFS-sharet `Tower-media` (`10.0.0.101:/mnt/user/media` → `/mnt/pve/Tower-media`)
er montert med `hard`-opsjon på to Proxmox-noder. Et heng på NFS-serveren gjør
at I/O blokkerer i flere minutter (`timeo=600`) i stedet for å feile raskt —
typisk symptom på at Emby/medieavspilling fryser uten klar feilmelding.

Workflowen sjekker derfor at mountet faktisk *responderer* (ikke bare at det er
montert), og remonterer det hvis det har hengt seg.

## Intervall og hva som utløser reparasjon

- **Hvert 5. min.** `scheduleTrigger` → SSH til begge nodene.
- **Reparasjon** utløses kun når helsesjekken feiler. Friske mount gir
  `tower-media: healthy` og ingen aksjon.

## Hvordan det fungerer (arkitektur)

N8n-noden `Check and repair Tower media` kjører **bare**:

```
ssh -i /home/node/.n8n/ssh/tower_media_ed25519 root@10.0.0.120 \
 && ssh -i /home/node/.n8n/ssh/tower_media_ed25519 root@10.0.0.103
```

Dette er **ikke** en tom kommando. Nøkkelen er låst i `authorized_keys` på begge
nodene med `command="/usr/local/sbin/n8n-tower-media-repair"` (pluss
`no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty`). Hver SSH
utløser altså det faste scriptet, uansett hva som står etter SSH.

Scriptet gjør i tur:

1. `flock` på `/run/n8n-tower-media-repair.lock` — ingen overlappende
   reparasjoner.
2. Helsesjekk: `timeout 8 stat /mnt/pve/Tower-media "/mnt/pve/Tower-media/3 Folder Emby"`.
   Svarer det innen 8 s og mappa finnes → `healthy`, exit 0.
3. Ved heng: noter hvilke avhengige CT-er som kjører, `pct shutdown --timeout 45`
   (fallback `pct stop`), `umount -l`, remount NFSv4, verifiser på nytt
   (exit 1 hvis fortsatt død), og `pct start` CT-ene igjen.
4. Utskrift: `tower-media: repaired; restarted=<ct-liste>`.

## Hvilke CT-er/tjenester den kan restarte

| Node | CT-er/tjenester som stoppes ved remount |
|---|---|
| pc6 (`10.0.0.120`) | 104 (media-downloaders), 109 (arr-stack + grafana m.m.), 151 (Emby), 152 (Roon) |
| pc9 (`10.0.0.103`) | 106 (periphery agent-node) |

**Merk:** en reparasjon tar Emby (CT151) ned i den tiden remounten pågår — det
er bevisst, fordi Emby leser fra nettopp dette mountet.

## Varslingsmål

`notify/mobile_app_1_iphone_r` (Home Assistant). Node `Only when repaired`
filtrerer slik at push kun skjer når `exitCode != 0` **eller** utskriften
inneholder `repaired;`. Friske kjøringer sender ingenting.

## Avhengigheter

| Avhengighet | Hvor den bor |
|---|---|
| SSH-nøkkel `tower_media_ed25519` (+ `.pub`) | n8n-containeren, `/home/node/.n8n/ssh/` — **ikke** i Git |
| forced-command-script `n8n-tower-media-repair` | `/usr/local/sbin/` på **begge** nodene (pc6 + pc9) |
| `authorized_keys` med `command=`-lås | `/root/.ssh/authorized_keys` på begge nodene |
| HA long-lived token | Notify-nodens `Authorization`-header (`REDACTED_HASS_TOKEN` i eksporten) |

## Gjenoppretting

1. **Workflows → Import from File**, velg
   `workflows/tower-media-nfs-health-repair.json`.
2. I `Notify iPhone`-noden: sett `Authorization`-header til
   `Bearer <reell HA-token>`.
3. Sørg for at SSH-nøkkelen og forced-command-scriptet finnes på nodene (over) —
   uten dem kjører bare `permission denied`, og reparasjonen skjer aldri.
4. Aktiver.

## Kjente feil / merknader

- **Live-ui-korrupsjon (funnet 5. okt):** i den kjørende workflowen er
  `$json`-referansene i `Only when repaired` blitt strippet til `.stdout`,
  `.error`, `.exitCode` — ugyldig JS som krasjer filteret, så push sendes aldri.
  Eksportfilen ovenfor har korrekt `$json`-form. Den kjørende instansen bør
  rettes tilbake til `$json.*` (eller re-importeres fra denne fila).
- NFS-remount med `hard`-opsjon: hvis serveren er nede, blokkerer selve
  `umount -l` + `mount` raskt; `stat`-sjekken med `timeout 8` er det som skiller
  «heng» fra «midlertidig treg».