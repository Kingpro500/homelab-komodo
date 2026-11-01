# Recipe services — pc9 CT116

- **CT:** 116 on pc9
- **IP:** `10.0.0.173`
- **Mealie:** `http://10.0.0.173:9925`
- **Tandoor Recipes:** `http://10.0.0.173:8080`
- **Deployment:** Komodo GitOps from `Kingpro500/homelab-komodo`

Mealie uses its recommended SQLite setup for a small installation and stores
all application data in `/opt/mealie/data`.

Tandoor uses PostgreSQL 16. Database files are stored in
`/opt/tandoor/postgresql`, media in `/opt/tandoor/media`, and static files in a
Docker volume. Database and Django secret values are supplied through the
Komodo stack environment and are not committed to Git.

Docker logs are rotated at 10 MB with three retained files per service.
