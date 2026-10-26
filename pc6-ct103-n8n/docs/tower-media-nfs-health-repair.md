# Media health: dype prober og avgrenset gjenoppretting

Deployet 23. oktober 2026. Workflow-ID: `tower-media-nfs-health-repair`.
Aktiv hvert femte minutt. Tidligere Emby-workflow `dK3dJJIQ7smvUy9v` er **deaktivert**;
den skal ikke reaktiveres parallelt. `emby_watch.py` beholdes som historisk/manuell
API-adapter, men har ingen egen cron-reparasjon i Hermes-jobbregisteret.

## Faktisk kjede og eierskap

n8n (CT310, .119:5678) → autentisert `POST http://10.0.0.135:9118/media/check`
→ fast Python-adapter → **begrenset SSH-nøkkel** → pc6-runner.
Adapteren godtar ingen VMID, kommando eller sti fra request-body.
Nøkkelen `/home/hermes/.ssh/id_ed25519_media_recovery` har på pc6
`restrict,from="10.0.0.135",command="/usr/local/sbin/n8n-tower-media-repair"`.
SSH-kommandoen kan ikke overstyres av klienten. Ingen nøkler i Git eller n8n.
Alle SSH-forbindelser verifiserer vertsnøkler. pc6→pc9 bruker klusterets
betrodde RSA-oppføring, `HostKeyAlias=pc9` og
`/etc/pve/nodes/pc9/ssh_known_hosts`; ingen blind nøkkelaksept.

| Tjeneste | Node/VMID | Kontroll |
|---|---|---|
| Emby .150:8096 | pc6/200 | API med gyldig versjon, konkret mediefillesing i LXC og Emby-Docker `/mnt` |
| Tunarr .123:8005 | pc6/250 | konkret mediefillesing + HLS-spilleliste → videosegment |
| Tunarr .122:8005 | pc9/106 | konkret mediefillesing + HLS-spilleliste → videosegment |

Begge verter: `findmnt` må bekrefte NFS/NFS4-kilden
`10.0.0.101:/mnt/user/media` på `/mnt/pve/Tower-media`. En avgrenset søking
(maks 1000 katalogoppføringer, dybde 5, kun `3 Folder Emby/James Bond`)
velger én eksisterende videofil og leser inntil 4096 byte. Ingen søking i hele NAS.
Gjestene må lese samme fil. Tunarr velger første konfigurerte kanal og leser
inntil 65536 byte av et faktisk segment med MPEG-TS/fMP4-signatur.
Dette beviser **ikke alle kanaler**, undertekster eller Emby-klientavspilling;
Emby testes med API og filåpning, ikke autentisert transkoding.
Streaming kan opprette vanlig midlertidig Tunarr-transkodingscache; ingen
probe oppretter, endrer eller sletter filer på mediedelingen.

## Reparasjonspolicy

- Emby er kun observasjon og varsling: aldri automatisk restart/reboot, heller ikke ved langvarig feil.
- Tre påfølgende mislykkede Tunarr-kontroller før gjestereboot (normalt ca. 10–15 min).
- Både node/VMID/navn/kjørestatus kontrolleres fra fersk Proxmox-inventar.
  Flyttet, renummerert eller bevisst stoppet gjest gir **ingen** start/reboot.
- Frisk NFS på gjestens vert er påkrevd. Tunarr krever i tillegg frisk Emby
  (API og konkret mediefillesing), også kontrollert rett før tiltak.
- Hard allowlist ved kommandogrensen: kun `(pc6,250)` og `(pc9,106)`.
  Emby `(pc6,200)` avvises før subprocess. Maks én gjest
  per kjøring, minst 30 minutter mellom forsøk og maks to forsøk per gjest
  i rullerende 24 timer. Forsøk lagres **før** reboot-kommandoen sendes.
- Frisk kontroll nullstiller feiltelleren, men **ikke** forsøksbudsjettet.
- Etter tiltak poller runneren og krever samme dype kontroll før `recovered`.
  Restarten alene er ikke suksessbevis.
- **Aldri** restart av router, Unraid, Proxmox-vert eller CT210; aldri
  automatisk unmount/remount, `umount -l`, rettighetsendring eller medieskriving.
- Ved feil i vertens NFS: varsle og eskaler til menneskelig vurdering av alle
  mount-konsumenter. En gammel bind-mount kan repareres ved godkjent gjestereboot
  når vertskilden igjen er frisk, men en dårlig vertsmount repareres ikke automatisk.

## Varig tilstand, varsling og feil

På pc6: `/var/lib/media-recovery/state.json`, `latest.json`, `events.jsonl` og
`lock`. Atomisk state-lagring, katalog 0700 og state 0600. `flock` hindrer
parallelle kontroller/tiltak. Logrotate `/etc/logrotate.d/media-recovery` beholder
12 ukesrotasjoner. n8n lagrer både vellykkede og feilede kjøringer.

Reparasjon, gjenoppretting og vedvarende feil går gjennom eksisterende
`POST /notify` på .135:9118 og dermed `notify_ha.py` sitt felles time-tak.
Friske kjøringer er stille. Runneren begrenser feilpåminnelser til én/time.
HTTP-nodefeil, SSH-feil, timeout og runnerfeil rutes til samme varselnode.
HTTP-kall har tre forsøk med fem sekunders mellomrom.
Et 200-svar fra `/notify` betyr at det felles leveransepunktet aksepterte
meldingen; den kan være undertrykt av time-taket, ikke nødvendigvis synlig push.

**Begrensning i installert n8n 2.41.5:** `executeCommand` er ikke tilgjengelig
(`Unrecognized node type`), derfor brukes HTTP-adapteren uten å åpne shell-noder.
API-et avviste tilkobling av generell Error Workflow med «no published version»
selv etter aktivisering/publisert versjons-ID. Testworkflowene er slettet.
Operative HTTP-/runnerfeil varsles og ble kjørt gjennom ekte n8n, men en total
n8n-stans, feil i selve Code-noden eller et samtidig bortfall av audit-/notify-
tjenesten kan ikke varsles gjennom denne samme kjeden. Overvåk tjenestene
utenfra. Vi hevder ikke at en slik generell feilhåndterer er installert.

## Verifisert

- Python: tolv tester i isolerte midlertidige kataloger, inkludert 72 timers simulert
  Emby-feil med varsling uten reboot/forsøksbudsjett, hard reboot-allowlist, gjentatte feil,
  NFS-avhengighet, endret identitet, cooldown, maksbudsjett og konkret målrettet
  mock-reboot med etterkontroll. Ingen mock-test bruker produksjonsstate.
- JavaScript: tre parsertilfeller og `node --check`.
- Frisk direkte kontroll og autentisert HTTP-adapter: begge NFS-verter,
  Emby API/LXC/Docker-lesing, begge Tunarr-videoer à 65536 byte. Ingen reboot.
- Ekte planlagt n8n-kjøring **51742**: `success`, alle tre tjenester friske,
  `actions: []`. Kjøring 51733 var også frisk; 51730 var korrekt låst/overlappet.
- Isolert n8n-feiltest **51737**: utilgjengelig test-URL, varselgrenen
  fullførte via eksisterende `/notify`. Testworkflowen er slettet.
- Kjøring 51740 feilet fordi audit-serveren ble restartet akkurat under testen;
  dette er ikke skjult. HTTP-retries ble lagt til og etterfølgende planlagt
  kjøring 51742 var frisk. Ingen medietjeneste ble stoppet i testene.
- Uautentisert `/media/check`: HTTP 401. Forsøk på vilkårlig SSH-kommando med
  adapterens nøkkel kjørte bare den faste helsekontrollen.
- Tidligere Emby-workflow lest tilbake som `active: false`.

## Gjenoppretting / rollback

Kilde: `pc6-ct103-n8n/scripts/media_recovery.py` og testfilene ved siden av.
På pc6 installeres runneren root-eid som `/usr/local/sbin/media_recovery.py`;
`media-recovery-entrypoint` installeres 0755 som både
`/usr/local/sbin/n8n-tower-media-repair` og `/usr/local/sbin/check-tower-media-nfs`.
Sistnevnte foreldede CT104-script er nå ufarlig alias til samme låste runner.
Installer logrotate-filen til `/etc/logrotate.d/media-recovery`.
Ved runner-oppdatering: ta backup, kompiler staging-filen uten å kjøre runneren,
installer atomisk og les tilbake SHA-256/kilde. Ikke start runneren manuelt som
deploytest: HLS-probene starter strømmer. Ingen Emby/Tunarr-restart kreves.
Ikke rull tilbake til en versjon som tillater automatisk Emby-restart.

På Hermes kopieres `media_recovery_adapter.py` til `.hermes/scripts/`.
Kjør `python3 scripts/install_media_endpoint.py` som hermes for idempotent
integrasjon i eksisterende audit-server. Denne er testet mot faktisk fil.
Installer egen ny SSH-nøkkel 0600 ved gjenoppretting (ikke kopier nøkkel fra Git),
og legg public key med nøyaktig forced-command-begrensning ovenfor i pc6s
`/root/.ssh/authorized_keys`. Behold eksisterende, verifisert `known_hosts`.
Restart audit-service med
`XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart homelab-audit`.

Importer scrubbet workflow-JSON, erstatt **begge** `REDACTED_AUDIT_TOKEN`
med gyldig eksisterende audit-token i privat n8n-lagring. JSON er en import-body
uten read-only-felter, hemmeligheter eller `description`. Aktiver og les tilbake
workflow, vent på en ekte planlagt kjøring og se dype resultater.
Ikke aktiver gammel Emby-workflow parallelt.

Trygg pause: deaktiver `tower-media-nfs-health-repair` i n8n først.
Behold state/forsøksbudsjett og logg. Ikke nullstill state for å tvinge nye reboot.
Originale verts-skript er bevart privat under
`/var/lib/media-recovery/backups/`; **ikke** gjeninnfør den gamle CT104-
`umount -l`-automatikken. De gamle `n8n-tower-media-repair-pc6/pc9` i repoet er
historiske, supersedert og skal ikke deployes som ny løsning.

## Til å leke med (uten produksjonseffekt)

```sh
cd pc6-ct103-n8n/scripts
python3 test_media_recovery.py
node test_media_workflow.js
```

Testene erstatter state, kommandoer og tjenester lokalt. Ikke fremprovoser stale
NFS eller restart fungerende gjester for å teste policy. Ingen nye IP-er, porter
eller tjenester er lagt til; derfor ingen topologi-/dashboardendring nødvendig.
