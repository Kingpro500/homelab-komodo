# PC1 full heng – varsel

## Formål

Oppdage mulig full PC1-heng uten å gjøre automatisk strømreset.

## Signalene

Workflowen kjører hvert minutt og sammenholder:

- PC1-gjestestatus fra `homelab-audit /nodes`
- GPU-exporteren på `10.0.0.112:9105`
- Home Assistant-status for `switch.pc1_ai`

Det kreves fem påfølgende feilrunder. Strømpluggen må fortsatt være på.
Deretter sendes ett varsel med én times cooldown. Workflowen slår ikke av
strømmen.

## Hvorfor ingen automatisk strømreset ennå

Dette er første sikre trinn. Vi må først samle ekte hendelser og se at
kombinasjonen skiller full PC-heng fra nettverks- eller tjenesteavbrudd. En
fysisk reset kan senere legges bak samme vakt, men bør ha en separat eksplisitt
terskel og lengre cooldown.

Workflow-ID: `XqFVyopKBfaxfVMh`.
Første planlagte kjøring er verifisert som `success`.
