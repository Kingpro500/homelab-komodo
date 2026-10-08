# Homepage — versjonsregister (VERSIONS)

**Politikk / mandat:** Hver meningsfylt endring av Homepage-config-en lager en ny
versjon i `versions/vNNN/` (snapshot av `config/`) og en rad i tabellen nedenfor.
Gamle versjoner **slettes aldri** — dette er det pålagte arkivet slik at ingenting
forsvinner og man alltid kan gjenopprette «hvordan det så ut før». (Git i
`homelab-komodo` er det tekniske vernelaget; `versions/` er den menneskelesbare
indeksen med linker.)

## Regel for nye versjoner

1. Kopier `config/{services,settings,docker,widgets,bookmarks}.yaml` → `versions/v0NN/`.
2. Legg til rad i tabellen, med nytt versjonsnummer, dato, commit og endring.
3. Oppdater `homepage/README.md` om nødvendig.
4. Commit både config-en og snapshot-et sammen.

## Indeks

| Versjon | Dato | Commit | Endring | Snapshot |
|---|---|---|---|---|
| v001 | 2026-10-08 | (restaurert) | Proxmox-gruppa (pc1/pc6/pc9/pve+Tower) **øverst**, fjerne ødelagte proxmox-widgeter, CDN-ikoner, dokcerstatus, hastighetsmetre, dockctl | [v001](v001/) |