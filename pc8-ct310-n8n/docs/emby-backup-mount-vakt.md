# Emby backup-mount vakt

Workflow-ID: `x7ZcV5d4KUuL5z3V`  
Status: aktiv  
Intervall: hvert 15. minutt

Workflowen kaller den eksisterende guarded media health-endpointen på
`10.0.0.135:9118/media/check` og varsler ved NFS-/mount-feil, inkludert
`Stale file handle` og read-only-filsystem. Samme feilfingerprint varsles
maksimalt én gang per seks timer.

Workflowen gjør **ikke** restart eller remount av Emby/CT200. Det er bevisst:
backup-mounten kan feile samtidig som Emby har aktive strømmer. Varslet skal
komme tidlig nok til at mounten kan repareres kontrollert.

Tokenet hentes fra n8n runtime-miljøet (`AUDIT_TOKEN`) og ligger ikke i Git.
