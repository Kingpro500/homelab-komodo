# Medieplattform: Emby og Tunarr

Sist kontrollert: 2026-11-03.

## Produksjon

| Tjeneste | Plassering | Adresse | Ansvar |
|---|---|---|---|
| Emby | PC6, CT200 | 10.0.0.150:8096 | Primær medieserver |
| Tunarr primær | PC6, CT250 | 10.0.0.123:8005 | Live-TV |
| Tunarr sekundær | PC9, CT106 | 10.0.0.122:8005 | Separat Live-TV-instans / kapasitet |
| Unraid media | Unraid | 10.0.0.101 | NFS-kilde, read-only for Tunarr |

Emby bruker offisielt image `emby/embyserver`. Tunarr bruker
`ghcr.io/chrisbenincasa/tunarr`. All deploy skal gå gjennom Komodo; Docker
skal aldri administreres manuelt på CT-ene.

## Sikkerhets- og driftprinsipper

- Emby restartes eller oppgraderes aldri som del av diagnose.
- Tunarr-instansene har hver sin `/config` og SQLite-database. De må aldri dele
  config-volum.
- Mediamounts skal være read-only. CT200 er satt til `mp0 ... ro=1` og dette
  får effekt ved neste kontrollerte restart.
- Versionerte image-tagger brukes i produksjon. Ikke bruk `latest`.
- PC9-Tunarr er canary ved Tunarr-oppgraderinger; PC6-Tunarr oppgraderes først
  etter at PC9 har bestått test.
- Emby og Tunarr oppgraderes aldri samtidig.
- Det tas database-/konfigurasjonsbackup før hver oppgradering.
- NFS/stale-mount-recovery må kun starte Tunarr etter fersk NFS- og Emby-helsesjekk.
  Den skal aldri restarte Emby automatisk.

## Kontrollert oppgradering

1. Sjekk aktive Emby-sesjoner og pågående Tunarr-strømmer.
2. Ta backup av den berørte tjenestens konfigurasjon.
3. Oppgrader kun én Tunarr-instans (PC9 først), via Komodo.
4. Verifiser HTTP, M3U, XMLTV og en faktisk HLS-avspilling.
5. Vent gjennom en programgrense før PC6-Tunarr oppgraderes.
6. Emby oppgraderes i eget vedlikeholdsvindu med konfigurasjonsbackup,
   helsesjekk og rollback-plan.

## Repo-mål

De nåværende Komodo-deployene har historiske run-directory-referanser. De
fungerer, men skal erstattes kontrollert med én eksplisitt kilde per stack:

```
stacks/media/emby/
stacks/media/tunarr-pc6/
stacks/media/tunarr-pc9/
docs/operations/
```

Migreringen gjøres som en Komodo-deploy med identiske bind-mounts, porter og
image-digest, én tjeneste om gangen. Gamle kataloger slettes aldri før ny
deploy er verifisert og en rollback-periode er passert.
