# Emby backup-mount vakt

Workflow-ID: `x7ZcV5d4KUuL5z3V`  
Status: aktiv  
Intervall: hvert 15. minutt

Workflowen kaller `10.0.0.135:9118/media/check`, som kjører
`pc6-media-recovery/media_recovery.py` på pc6. Rapporten har en egen seksjon
`services["emby-backup"]` (mount OK, alder på siste vellykkede backup,
tjenestestatus, reparasjoner siste døgn).

Endret 2026-11-22 etter at backupen feilet stille i ni dager: den gamle
filteret lette etter `stale file handle` i en rapport som aldri sjekket
backup-mounten, og varslet derfor aldri.

- **Reparasjon** gjøres av runneren på pc6, ikke av n8n: re-bind av
  `/var/lib/emby-backups` i CT200s mount-navnerom og ny backup hvis den forrige
  er over 20 t gammel. Emby restartes **ikke**, og Emby-containeren bruker ikke
  backup-stien. Varsel om utført reparasjon kommer fra *Media health*-flyten.
- **Denne flyten** varsler bare når Emby-backupen fortsatt er syk (eller sjekken
  feiler), maks én gang per seks timer per tilstand, og én gang når den er frisk
  igjen.
- **Advarselsiden** i kartet får Prometheus-alarmene i gruppen
  `emby-config-backup`, også når vakten kjører uten å rette feilen
  (`EmbyBackupWatchNotFixing`) eller har sluttet å kjøre (`EmbyBackupWatchSilent`).

Tokenet hentes fra n8n runtime-miljøet (`AUDIT_TOKEN`) og ligger ikke i Git.
