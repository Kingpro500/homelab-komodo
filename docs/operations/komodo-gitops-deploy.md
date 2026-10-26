# Komodo + GitHub: én deploymodell

Dette dokumentet er fasiten for nye tjenester, inkludert `pc9-observability`
(CT104, `10.0.0.126`).

## Ansvarsdeling

```text
GitHub / homelab-komodo  -> versjonert kilde for Compose, config og README
Komodo Core              -> velger server, secrets, deploy, status og historikk
Periphery i mål-CT       -> utfører Komodo-kommandoer
Docker i mål-CT          -> kjører bare containerne Komodo deployer
```

Git er aldri en kopi av containerdata. Komodo er aldri stedet for den eneste
kopien av Compose-filer. En tjeneste er ikke ferdig før den både er dokumentert
i Git og vises som frisk i Komodo.

## Ny isolert CT

1. Opprett en uprivilegert Debian LXC med `nesting=1,keyctl=1`, fast IP,
   `onboot=1` og ressurser tilpasset tjenesten.
2. Installer Docker/Compose én gang som bootstrap. Dette er ikke en
   applikasjonsdeploy.
3. Opprett en **kortlivet, privilegert V2 onboarding key** i Komodo.
4. Installer én Periphery-agent. Bruk enten eksisterende container-modell eller
   native `periphery.service` - aldri begge.
5. Bekreft `Logged in to Komodo Core` og serverstatus `OK`.
6. Fjern onboarding-keyen fra CT og slett den i Komodo. Behold
   Periphery-identiteten (`/etc/komodo/keys/periphery.key` for systemd).

Detaljert bootstrap-mal: `templates/lxc-komodo-v2/README.md`.

## Ny stack eller endring

1. Lag mappe `<host>-ct<id>-<service>/` i Git med `docker-compose.yml`,
   konfigurering og README.
2. Legg hemmeligheter bare i Komodo Secret Variables. Aldri i Git, `.env`,
   logger eller chat.
3. Valider Compose, commit og push bare den aktuelle endringen.
4. Opprett/oppdater stacken i Komodo med repo, branch og riktig `run_directory`.
5. Deploy fra Komodo. Ikke kjør en separat `docker compose up` i
   stack-mappen.
6. Verifiser helseendepunkt, persistens, ressursbruk og Komodo-status. Oppdater
   README/inventar før arbeidet avsluttes.

## Feil og gjenoppretting

- Diagnose før handling. Stopp ved uklar target-server, feil run-directory eller
  manglende Periphery-forbindelse.
- En feil deploy skal ikke erstattes med en «v2»-stack. Reparer eller slett den
  inaktive registreringen først, så Komodo har én autoritativ stack.
- Ikke slett Periphery-key eller persistent Docker-volumer ved vanlig feilretting.
- Hvis Komodo ikke kan deploye, reparer Core ↔ Periphery-forbindelsen først;
  ikke omgå den med manuell Compose.
