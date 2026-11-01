# Navidrome — pc9 CT114

- **CT:** 114 on pc9
- **Address:** `http://10.0.0.172:4533`
- **Deployment:** Komodo GitOps from `Kingpro500/homelab-komodo`
- **Data:** `/opt/navidrome/data` by default
- **Music:** `/opt/navidrome/music` by default, mounted read-only in the container

Optional Komodo variables:

- `NAVIDROME_DATA_PATH`
- `NAVIDROME_MUSIC_PATH`
- `NAVIDROME_UID` and `NAVIDROME_GID`
- `TZ`

Set `NAVIDROME_MUSIC_PATH` to the CT path containing the actual music library.
The library must remain outside Git and should be mounted read-only.
