# Homepage — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-homepage`
- **Address:** `http://10.0.0.128:3009`
- **Runtime config:** `/opt/homepage`

Tower's prior Homepage YAML configuration is copied once as runtime data and is
kept out of Git because it can contain integration credentials. Required Komodo
variable: `HOMEPAGE_CONFIG_PATH=/opt/homepage`.

## services.yaml er GitOps — med et forbehold

`docker-compose.yml` mounter fila fra repoet:

```yaml
- ../homepage/config/services.yaml:/app/config/services.yaml:ro
```

Fila i git er det Homepage serverer, og mounten er read-only. Men det er en
felle ved endringer, funnet og verifisert 4. oktober 2026:

**Komodo henter ikke `services.yaml` fra repoet.** Stackens `file_paths` er bare
`['docker-compose.yml']`, så Komodo synkroniserer kun den filen. Redeploy
trekker riktig commit — `deployed_hash` matcher — men `services.yaml` som
serveres ligger i repo-klonen på verten, mountet relativt til `run_directory`.

Konsekvens i praksis: en commit til `services.yaml` plukkes ikke opp av en vanlig
redeploy. Etter endring må den klonede fila på verten oppdateres eksplisitt.

Verifisert 4. oktober 2026: etter redeploy med `deployed_hash: 0247141` serverer
`/api/services` fortsatt den gamle `Monitoring`-gruppen uten Netdata-oppføringene,
mens git har dem. Lokale agenter ble kontrollert OK (HTTP 200 på port 19999), så
lenkene er gyldige — de er bare ikke blitt publisert.

## Endre services.yaml

1. Endre `homepage/config/services.yaml` i git og push.
2. Oppdater klonen på verten som mounten peker på — enten ved å trekke commiten
   dit, eller ved å redeploye med `reclone` slik at Komodo bygger klonen på nytt.
3. Kontroller med `curl -s http://10.0.0.128:3009/api/services | grep -i netdata`.

Steg 2 er det som mangler ved en vanlig redeploy. Strukturen i fila er
`icon` / `href` / `description` per oppføring, med 4 mellomrom for oppføringsnivå
og 8 for feltene. PyYAML finnes ikke på CT157, så valider lokalt med en
indentasjonssammenligning mot en eksisterende oppføring.

## Relatert

- `homepage/config/services.yaml` — live tjenesteliste
- `migration-backlog.md` — oppføringen «Homepage» og GitOps-forbeholdet