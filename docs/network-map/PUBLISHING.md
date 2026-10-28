# Trygg publisering av nettverkskartet

## Regel

`origin/main` er den eneste publiseringskilden. Ingen skal kopiere en lokal
eller tilfeldig serverfil rett til den levende siden. Dette er spesielt viktig
etter at en ufullstendig v2.014-fil erstattet den komplette kart-layouten.

## Planlagt først

Før en CT/VM, Docker-stack eller tjeneste flyttes, opprettes eller vesentlig
endres, skal den føres i kartets gjeldende kilde som **Planlagt**. Oppføringen
skal si hva som skal skje, mål-node, planlagt CT/VM-ID og IP når dette er
kjent, samt viktige avhengigheter. Dette gjelder også når arbeidet ennå bare
er under utredning.

Etter teknisk verifisering endres den samme oppføringen til aktiv i en **ny**
kartversjon. Ikke vent med kartoppføringen til arbeidet er ferdig, og aldri
fjern historikken for den planlagte endringen.

Den aktive nginx-containeren `nettkart` kjører i **CT120** (`10.0.0.124`) og
serverer bind-mounten:

`/opt/komodo/stacks/pc6-ct120-web/docs/network-map` →
`/usr/share/nginx/html` (read-only i containeren).

CT120 er den renummererte tidligere CT104. Se
[`id-renumbering-2026-10-21.md`](../id-renumbering-2026-10-21.md) for hele
ID-mappingen.

## Automatisk publisering

Når en endring er merget til `main`, bruker den verifiserte Komodo-flyten
stacken `pc6-ct120-web`:

1. `POST /read/ListStacks` — finn stack-ID-en.
2. `POST /execute/PullStack` med `{"stack":"<id>"}`.
3. Vent på `POST /read/GetStackActionState` til `pulling:false`.
4. Les `POST /read/GetStack` og fortsett bare når `latest_hash` er en konkret
   commit og `remote_errors` er tom.
5. Kjør `POST /execute/DeployStack` med samme stack-ID.
6. Verifiser `deployed_hash == latest_hash` og les live-HTML tilbake.

Dette er den operative publiseringsflyten. GitHub Actions validerer innholdet,
men er ikke en deploy-garanti. GitHub-merge alene publiserer ikke kartet.

## Komodo

Komodo kan brukes til å kjøre den samme kommandoen som en kontrollert deploy-
handling på CT120. Den skal peke på dette Git-repoet og kjøre skriptet over —
ikke kjøre `cp`, `git reset --hard`, eller synkronisere en lokal arbeidskopi.
Før en Komodo-stack eller prosedyre opprettes må den verifiseres mot den
eksisterende `nettkart`-containeren, slik at den ikke oppretter en konkurrerende
container på port 3020.


## Faste kartregler

I tillegg til den kontrollerte deployen gjelder dette alltid:

1. Git-commit er historikken. Ikke stopp en liten rettelse for å lage manuell versjonsmappe.
2. Oppdater versions/index.html bare når en egen lesbar arkivside faktisk trengs.
3. Verifiser node, VMID/CTID, kjørestatus, IP og port mot Proxmox/Docker før commit.
4. Én CT/VM-boks skal ligge på riktig fysisk node. Flytt hele boksen, aldri en midlertidig oppsummeringstabell.
5. Bruk én stor svart tjenesteboks per CT/VM; seks tjenester per rad på bred skjerm og to på smal skjerm.
6. Tjenestenavnet skal være klikkbart direkte til IP:port. Ikke vis separat IP- eller merknadskolonne.
7. Statuslys og av/på-kontroller beholdes inne i tjenesteboksen. Ikke fjern eller skjul st-wrap, g-ctl eller fillStaticRows().
8. Feil rettes med en ny commit. Aldri overskriv eller slett Git-historikken, og bruk alltid publiseringsskriptet.
