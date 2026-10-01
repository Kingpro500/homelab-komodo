# Audiobookshelf — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-audiobookshelf`
- **Address:** `http://10.0.0.128:13378`
- **Runtime data:** `/opt/audiobookshelf/config`
- **Library:** Tower media mounted read-only at `/scan/media/Video/Z Audiobook`.

Only Tower appdata is copied for migration; audiobook media is never copied or
modified. Required Komodo variable:
`AUDIOBOOKSHELF_CONFIG_PATH=/opt/audiobookshelf/config`.
