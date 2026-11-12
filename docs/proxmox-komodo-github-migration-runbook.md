# Proxmox → Komodo → GitHub: flytting og avviksrevisjon

Dette er den obligatoriske rutinen ved flytting, omdøping eller gjenbruk av en CT. En Proxmox-flytting er **ikke ferdig** når CT-en starter på ny node. Den er ferdig først når identitet, Periphery, Komodo-server, Komodo-stacker, GitHub-kilde og driftspassasje er kontrollert samlet.

## Hvorfor den gamle rutinen feilet

Tidligere rutiner beskrev opprettelse og deploy, men hadde ikke en hard sperre mot å flytte bare gjesten. De brukte også navn som om de beviste tilknytning. Det er feil:

- En Komodo-server kan være `Ok` og likevel være koblet til feil CT.
- En stack kan ligge på riktig GitHub-repository, men ha feil `config.server_id`.
- `ListStacks`-listen er et sammendrag; `server_id`, repo og run directory må leses fra `GetStack`.
- CT-navn, stack-navn og run directory er forskjellige felt og må sammenlignes eksplisitt.
- En deploy-aksept betyr bare at Komodo har køet operasjonen; den beviser ikke at tjenesten kjører.
- GitHub-repositoryet er kilden for compose og dokumentasjon, men flytter ikke Komodo-registreringen eller Periphery.

## Ufravikelig regel

**Ingen agent skal flytte, opprette eller ta over en CT uten å lage en før/etter-inventar for hele kjeden og stoppe ved avvik.** Ved avvik skal agenten dokumentere funnet i nettverkskartet før neste muterende handling. Ikke registrer en ny Komodo-server som snarvei; finn og reparer den eksisterende tilknytningen.

## Identitetsmodell

For en vanlig CT skal disse verdiene stemme:

| Felt | Forventning |
|---|---|
| Proxmox | fysisk node + CTID + gjestenavn |
| Komodo server | nøyaktig `<node>-ct<id>-<navn>`, én server per CT |
| Komodo server-id | eksisterende `server_id` for den faktiske Periphery-instansen |
| Stack | tjenestenavn, med `config.server_id` som peker på riktig Komodo-server |
| Stack run directory | repoets katalog for samme mål-CT; ikke en gammel node/CT |
| GitHub | korrekt repo, branch og `file_paths`; ingen uautorisert lokal compose som kilde |
| Gjestedata | Periphery kjører og svarer fra CT-en som faktisk ligger på målnoden |

Unntak må navngis og dokumenteres. CT110/Core og eldre systemd-Periphery er kjente unntak, ikke grunn til å gjette.

## Før flytting (lesende kontroll)

1. Les `AGENTS.md`, `docs/ACCESS-RUNBOOK.md`, siste nettverkskart og drift-vakten.
2. Hent Proxmox-inventar fra clusteret: CTID, navn, node, status og IP.
3. Hent Komodo `ListServers`, og for hvert relevant treff `GetServer`. Lagre bare navn, id, state og endpoint-status i arbeidsnotater.
4. Hent `ListStacks`, og deretter `GetStack` for **hver** stack som tilhører CT-en. Kontroller `config.server_id`, `config.repo`, `branch`, `run_directory`, `file_paths`, `info.missing_files` og `info.remote_errors`.
5. Kontroller GitHub remote/branch og at forventet stack-katalog og compose-fil faktisk finnes i repoet.
6. Kontroller Periphery på gjesten: Docker-standarden under `/opt/komodo/periphery/`, eller dokumentert eldre systemd-variant under `/etc/komodo`.
7. Ta konfigurasjonsbackup. For Emby: kontroller aktive strømmer og ikke stopp/restart under streaming.
8. Hvis noen av punktene ikke kan bekreftes: stopp. Ikke flytt og ikke opprett duplikat.

## Flytting: transaksjonell rekkefølge

1. Merk planlagt flytting og alle kjente avvik i nettverkskartet.
2. Stopp bare tjenester/CT-er etter helse- og avhengighetskontroll. Emby følger egen strengere prosedyre.
3. Flytt CT-en i Proxmox.
4. Verifiser på målnoden: CTID, navn, nettverk/IP, mounts, disk og at gjestens Periphery er den samme instansen.
5. **Ikke** kjør `ct-komodo` på nytt og **ikke** lag ny Komodo-server dersom CT-identiteten er den samme.
6. Oppdater eksisterende Komodo-server kun dersom navn eller Periphery-konfigurasjon faktisk må korrigeres. Bekreft serverens id og state med `GetServer`.
7. Oppdater hver berørt stack med korrekt `config.server_id`, repo, branch, run directory og file paths. Dette gjøres via dokumentert Komodo API/UI, ikke ved håndredigering av intern database.
8. Pull/deploy bare etter at koblingene er kontrollert. Verifiser `missing_files=[]`, `remote_errors=[]`, forventet `deployed_hash` og faktisk container/endpoint.
9. Oppdater GitHub-dokumentasjon og nettverkskartet i samme endringsrunde. Commit, push/PR, merge og publisering/deploy skal rapporteres som separate verifiserte steg.

## Etterkontroll / godkjenningskriterier

En flytting kan først lukkes når alle disse er sanne:

- Proxmox viser CT-en på forventet node og med forventet CTID/navn.
- Periphery svarer fra denne CT-en.
- Det finnes nøyaktig én Komodo-server for CT-en, med forventet navn og `Ok` når CT-en er tilgjengelig.
- Alle berørte stacks peker med `config.server_id` til denne serveren.
- Ingen stack har gammel node/CT i navn, run directory eller compose-mounts uten dokumentert grunn.
- GitHub repo/branch/file paths er forventet, og arbeidskopien er ren og synkronisert.
- Komodo viser ingen manglende filer eller remote-feil.
- Tjenesten er helsesjekket på riktig endpoint.
- Nettverkskart, runbook og eventuell driftsvakt er oppdatert.

## Revisjonskommandoer

Kjør fra en autorisert Komodo-rute. Hold credentials prosesslokale og skriv aldri tokens til output, filer eller commit. `ListStacks` alene er ikke nok:

```sh
# Proxmox – clusterinventar
pvesh get /cluster/resources --type vm --output-format json

# Komodo – les servere og stacks
POST /read/ListServers {}
POST /read/ListStacks {}
POST /read/GetServer {"server":"<server_id>"}
POST /read/GetStack {"stack":"<stack_id>"}
```

For hver stack skal revisjonen sammenligne `GetStack.config.server_id` med `GetServer.id`, ikke bare sammenligne tekst i navn. Resultatet skal være en tabell med kolonnene `ctid`, `proxmox_node`, `ct_name`, `server_name`, `server_id`, `server_state`, `stack_name`, `stack_server_id`, `repo`, `run_directory`, `missing_files`, `remote_errors`, `status`.

## Registrerte avvik i revisjonen 2026-11-12

Dette er en arbeidsliste fra live-lesing av Proxmox og Komodo. Den skal ikke tolkes som rettet før hvert punkt er kontrollert og lukket. Full maskinlesbar revisjonsrapport fra 2026-11-12 ligger i `docs/proxmox-komodo-github-live-audit-2026-11-12.md`:

- Komodo har servere med `NotOk` eller `Disabled`, blant annet flere `pc1`-CT-er, `pc6-ct111-iventoy`, `pc6-ct140-iventoy`, `pc6-ct150-browsers`, `pc6-ct153-immich`, `pc6-ct154-paperless`, `pc6-ct215-tubearchivist` og den gamle `pc6-ct151-emby`-registreringen.
- Det finnes en åpenbar duplikat/gammel Emby-registrering: `pc6-ct151-emby` er `Disabled`, mens aktiv server er `pc6-ct200-emby`. Den gamle må ikke slettes før eierskap og eventuelle stacks er verifisert.
- Flere stacks peker til feil Komodo-server: alle/majoriteten av `pc6-ct109-*` ligger samlet på `pc6-ct109-node` (noen peker også til `pc6-ct340-krusader`), selv om stacknavnet sier tjenesten. Dette må vurderes mot faktisk compose-layout før korrigering.
- `pc6-ct115-unifi` peker til server `pc7-ct115-unifi`, mens stackens run directory er `pc6-ct155-unifi`; Proxmox/Komodo/GitHub må avstemmes før endring.
- Flere `pc6-ct120-*`-stacks peker til server `pc6-ct120-monitoring`, mens enkelte run directories peker til `pc8-ct102-*`, `pc6-ct104-*` eller `pc6-ct109-*`. Dette er migreringsspor som må bekreftes, ikke masseflyttes blindt.
- `pc6-ct123-metube` peker til `pc6-ct123-ct123`, men run directory er `pc6-ct104-media-downloaders`.
- `pc6-ct200-alloy` ligger på serveren `pc6-ct200-emby`; dette kan være tilsiktet sidecar, men må dokumenteres eksplisitt.
- `pc6-ct250-alloy` og `pc6-ct250-nfs-health` ligger på `pc6-ct250-tunarr`; også dette må dokumenteres som sidecar eller korrigeres.
- Flere stacks mangler `deployed_hash`, mens andre har `latest_hash` som avviker fra deployet hash. Dette er ikke nødvendigvis feil, men skal forklares og helsesjekkes før status settes grønn.
- `ct118-gitea` og `pc6-ct117-clickhouse` hadde `remote_errors`; disse skal undersøkes separat før deploy.

Ingen av disse avvikene skal «repareres» ved å lage nye servere eller stacks. Først bygges en navngitt mapping mellom faktisk Proxmox-CT, Periphery, Komodo-server og stack.
