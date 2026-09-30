# GroveMap

WizTree-like, read-only disk usage analysis for Tower shares.

- **Komodo server:** `pc6-ct109-node`
- **Address:** `http://10.0.0.128:8080`
- **Data:** Tower `media`, `photos`, and `backups` shares, mounted read-only.

The first scan is started manually from the GroveMap UI. Scan results are
cached for one hour. GroveMap cannot modify Tower files.

This reports usage by Unraid share. It does not reveal which physical Unraid
array disk holds an individual file; that requires separately exposing
individual disk paths read-only.
