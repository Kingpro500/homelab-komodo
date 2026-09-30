# Immich — pc6 CT 153

- **CT:** 153 on pc6
- **Address:** `10.0.0.126:2283`
- **Photos:** remain on Tower and are mounted read-write at `/photos` in the CT.
- **PostgreSQL data:** `/opt/immich/postgres` in the CT.
- **Runtime secrets:** stored as secret Komodo variables; the temporary CT-local `.env` is never committed.
- **GPU:** Intel render device is passed through for Immich acceleration.

The pinned images deliberately match the previous Tower deployment. The model cache is disposable and rebuilt locally.
