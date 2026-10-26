# Komodo stack-deployment runbook

## Formål

Alle stacker skal kunne synkroniseres, valideres og deployes uten å gjette hvilken
working copy, compose-fil eller miljøkonfigurasjon Komodo bruker.

## Før en stack opprettes

1. Velg én repo-layout og bruk den konsekvent:
   - `Run Directory: <stack-directory>`
   - `Compose File: docker-compose.yml`
2. Bekreft at filen faktisk finnes i GitHub på den kombinasjonen.
3. Opprett og dokumenter nødvendige secrets i Komodo Environment. Verdier skal
   aldri legges i Git eller chat.
4. Valider Compose-filen med samme Compose-versjon som Periphery bruker.
5. Kontroller at serveren, Periphery og repo-bindingen er operative.

## Standardkonfigurasjon for homelab-komodo

For `pc6-ct340-additional-services` er riktig konfigurasjon:

```text
Repo: Kingpro500/homelab-komodo
Branch: main
Run Directory: pc6-ct340-additional-services
Compose File: docker-compose.yml
```

Ikke bland denne med en repo-root-konfigurasjon (`Run Directory: .` + en filsti
med stack-prefiks). Velg én variant og test den før deploy.

## Obligatorisk repo-cache-preflight

Kjør kontrollen på klonen Komodo faktisk bruker før PullStack. For en delt
reporessurs er dette vanligvis Core sin repo-cache; en ny stack får ikke en ny,
isolert repo-cache.

Kontroller:

1. working tree er ren (git status --short --branch);
2. ingen rebase-merge, rebase-apply, MERGE_HEAD, CHERRY_PICK_HEAD eller
   index.lock finnes;
3. origin/main er nåbar;
4. HEAD og origin/main sammenlignes med
   git rev-list --left-right --count HEAD...origin/main;
5. lokal branch kan fast-forwardes, eller divergensen er eksplisitt vurdert;
6. lokale Komodo-commits identifiseres med git log origin/main..HEAD.

Hvis lokal branch er både foran og bak, skal ikke git pull --rebase gjentas
blindt. Ta først en gjenopprettbar Git bundle av alle refs, og noter sti og
commit. Først deretter kan en kontrollert fast-forward, reset av kun den
midlertidige cachen eller reclone vurderes. Ingen lokal Komodo-commit skal
overskrives uten backup.

## Pull → validate → deploy

1. Kjør `PullStack`.
2. Vent til operasjonen er ferdig, og les tilbake `GetStack`.
3. Krev at `latest_hash` er en konkret commit og at `remote_errors` er tom.
4. Hvis `latest_hash` er tom, skal deploy ikke forsøkes.
5. Kjør Compose-validering og kontroller manglende `${VAR:?message}`-variabler.
6. Deploy bare den aktuelle stacken.
7. Les tilbake `GetStack`, `GetStackActionState` og containerstatus.
8. Kontroller logger og health-endepunkter før stacken meldes som ferdig.

## Diagnostikk ved avvik

Skill alltid mellom:

- repo-cache (`/opt/komodo/repos/<repo>`),
- stack-working-copy (`/opt/komodo/stacks/<stack>`),
- faktisk compose-fil,
- Komodo Core-operasjon,
- Periphery-operasjon.

Hvis Core viser en Git-feil som ikke finnes i working copy:

1. Ikke slett `.git` eller stacken.
2. Les Core- og Periphery-loggene rundt samme task-ID.
3. Les `GetStackActionState`.
4. Sammenlign commit, branch, remote og compose-sti i alle kloner.
5. Lagre stack-konfigurasjonen på nytt og kjør én ny PullStack.
6. Hvis operasjonen fortsatt ikke når Periphery, opprett en ny stack med samme
   repo/server etter at den gamle runtime-stacken er dokumentert. Slett ikke den
   gamle før den nye er verifisert.

## Hendelse 26. oktober 2026: CT340

Den faktiske rotårsaken lå i Komodo Core sin delte repo-cache, ikke i CT340:

- Core-cachen hadde en lokal Komodo-generert commit (7fac8ff) som slettet en
  Glance-fil.
- Cachen var samtidig 179 commits bak origin/main.
- git pull --rebase feilet på grunn av divergensen. Den tidligere
  rebase-merge-meldingen var lagret operasjonsstate; ingen aktiv rebase-lås
  fantes da cachen ble undersøkt.
- Stack-working-copyen på CT340 var ren, så rydding der kunne ikke løse feilen.
- En ny stack arvet feilen fordi begge stackene brukte samme delte reporessurs
  og dermed samme Core-cache.
- Den lokale committen ble bevart i
  /backups/homelab-komodo-core-cache-before-repair-20261026.bundle før kun
  Core-cachen ble synkronisert til origin/main.
- Etterpå ble latest_hash kjent og remote_errors tom.
- Authentik måtte pinne ghcr.io/goauthentik/server:2026.8.5 fordi :latest ikke
  finnes.
- Gatus krevde config.yaml, og NetAlertX krevde dagens /data-layout og
  nettverkskapabiliteter før begge var stabile.

En ny stack frisker stackidentiteten, men reparerer ikke en korrupt eller
divergerende delt reporessurs.

## Secrets

Compose-filer kan kreve variabler som:

```text
AUTHENTIK_SECRET_KEY
AUTHENTIK_POSTGRESQL_PASSWORD
VAULTWARDEN_ADMIN_TOKEN
```

Komodo skal vise at hver variabel finnes før deploy. Rapporter bare variabelnavn
og `configured: true/false`; aldri verdier.

## GitHub-credentials

GitHub-token skal ikke ligge i klartekst i `git remote -v`. Bruk Komodo sin
Git-provider/account-binding eller en credential helper. Etter oppdaget token i
remote-URL skal tokenet roteres og remote verifiseres uten credential i URL-en.

## Sikkerhetsregler

- Ingen `DestroyStack`, `docker compose down`, `git reset --hard` eller `git clean`
  under diagnostikk.
- Ikke restart Emby eller andre produksjonstjenester uten stream-sjekk.
- Bruk SSH/Proxmox-konsoll som leseorientert diagnostikktilgang først.
- Bekreft faktisk runtime etter enhver ekstern state-endring.

## Ferdig-kriterier

En deploy er ikke ferdig før alle punktene er verifisert:

- GitHub commit er kjent.
- `latest_hash` og `deployed_hash` stemmer.
- `remote_errors` er tom.
- Compose-prosjektet finnes på riktig server.
- Forventede containere kjører.
- Watchtower og Diun er kontrollert separat.
- Homepage, nettverkskart og denne dokumentasjonen er oppdatert i samme commit.