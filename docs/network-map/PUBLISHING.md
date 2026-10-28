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

Når en endring er pushet til `main`, skal Komodo-stacken `pc6-ct120-web`
kjøre PullStack og deretter publiseringskommandoen på CT120. Det kreves ingen
manuell godkjenning og ingen separat versjonsbestilling utover historikken i
Git. GitHub Actions validerer kun innholdet etter oppdateringen av `main`.

Komodo-handlingen skal bruke:

```sh
/usr/local/sbin/deploy-network-map
```

og kjøre den først etter at `PullStack` er ferdig og `latest_hash` er en
konkret commit uten `remote_errors`. Dette er den faktiske deploy-triggeren;
en GitHub Actions-kall direkte til CT120 brukes ikke.

Publiseringsjobben bruker den samme arbeidskopien som nginx faktisk har
bind-mountet, henter `origin/main`, og validerer at kandidaten har:

- versjonsnummer;
- full serviceoversikt;
- VM/CT-rammer (`data-vmid`);
- det pålagte node-sammendraget og `/nodes`-integrasjonen.

Det nekter også å publisere lavere versjon enn den levende siden. Før hver
publisering lagres den nåværende live-filen i
`/var/lib/nettkart/backups/` på CT120. Nginx trenger ikke restart fordi den
leser den erstattede statiske filen på neste HTTP-kall.

Manuell fallback

Ved behov kan samme publisering startes på CT120:

```sh
ssh <admin>@10.0.0.124 /usr/local/sbin/deploy-network-map
```

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
