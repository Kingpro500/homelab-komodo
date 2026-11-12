# ntfy — pc9 CT111 (10.0.0.155)

| | |
|---|---|
| **Komodo-server** | `pc9-ct111-ntfy` (systemd-Periphery) |
| **Komodo-stack** | `pc9-ct111-ntfy`, `project_name = pc9-ct111-ntfy` |

Varseltjener. Nettverkskartet kalte den «historisk reserve · stoppet på pc9»
fram til 12. nov 2026, men containeren har kjørt hele tiden.

## To ting som ikke må endres uten videre

**`project_name = pc9-ct111-ntfy`.** Volumene er navngitte og heter derfor
`pc9-ct111-ntfy_ntfy-cache` og `pc9-ct111-ntfy_ntfy-data`. Et nytt
prosjektnavn gir tomme volum — abonnementer og brukere forsvinner.

**`NTFY_BASE_URL`** settes i Komodo og må være adressen klientene bruker.
Den havner i lenkene og vedleggs-URL-ene ntfy sender ut. Verdien sto på
`http://10.0.0.131` til 12. nov 2026, en adresse som ikke svarer: CT111 fikk
`.155` da CT320 overtok `.131`. Rettet til `http://10.0.0.155`.

## Historikk

Stacken var definert direkte i Komodos database (`file_contents` i
grensesnittet), ikke i Git. Flyttet hit 12. nov 2026, så drift-vakten ser den
og endringer går gjennom `homelab-pr`.
