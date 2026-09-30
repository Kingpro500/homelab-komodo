# Paperless-ngx — pc6 CT154

- **Komodo server / stack:** `pc6-ct154-paperless`
- **Address:** `http://10.0.0.131:8000`
- **Runtime data:** `/opt/paperless/` inside CT154; never committed to Git.
- **Services:** Paperless-ngx, PostgreSQL, Valkey, Gotenberg and Tika.

Komodo holds the database password and Paperless secret key as secret variables.
The first visit to the web interface prompts for the initial superuser. Upload
or drop documents into the Paperless consume directory only after that account
has been created.

The full document archive, database and exports live on CT154's dedicated
64 GB Proxmox disk and are included in CT-level backup planning. Do not delete
or recreate these paths when updating the stack.
