# Threadfin — pc9 CT107

- **Komodo server:** `pc9-ct107-threadfin-test`
- **Komodo stack:** `pc9-ct107-threadfin-test`
- **Host:** pc9 / Proxmox CT 107
- **Address:** `10.0.0.130`
- **Web UI:** `http://10.0.0.130:34400/web/`

Threadfin is deployed through Komodo from this repository. Tuner, XMLTV and
M3U source URLs are configured in the persistent named volume through the web
UI. No secrets belong in Git.

Do not run `docker compose up` manually as the deployment method; push to
GitHub and reconcile the Komodo stack instead.
