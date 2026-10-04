# Cleanuparr — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-cleanuparr`
- **Address:** `http://10.0.0.128:11011`

Cleanuparr cleans up the *arr queues: stalled and metadata-stuck downloads,
failed imports, files that trip the malware blocklist, and orphaned files. It
talks to Deluge as the download client and to Sonarr/Radarr for what is wanted.

## What it is wired to

Everything lives on CT109 already, so Cleanuparr joins them there rather than on a
new container:

| Service | Address | Role |
| --- | --- | --- |
| Deluge | `10.0.0.128:8112` | download client |
| Sonarr | `10.0.0.128:8989` | queue owner, series |
| Radarr | `10.0.0.128:7878` | queue owner, films |

Prowlarr and Bazarr are not queue owners and are not configured.

**Readarr is deliberately left out.** It is the one stack whose paths do not line
up: Deluge, Sonarr and Radarr all bind the host's `/data` at `/data`, but Readarr
binds the host's `/data/z downloads` at `/data`. Readarr therefore reports its
downloads as `/data/...`, which inside Cleanuparr — mounted on `/data` — would
resolve to the wrong directory. Since Cleanuparr can delete what it resolves, that
mismatch is a data-loss risk, not a cosmetic one. Readarr can be added once its
mount is aligned with the others.

## The shared download tree

`/data` is mounted read-write, because orphan removal deletes from it. That is the
only path Cleanuparr can act on outside the Deluge API, and it is the same host
volume the media stack already uses.

## Secrets

`config.json` inside the `cleanuparr-config` volume holds the Deluge and *arr API
keys. It is deliberately **not** in the repo and not bind-mounted from it — it is
generated on the host and lives only in the Docker volume. Nothing sensitive is in
Git.

Deluge currently has no web password set, which is why Sonarr and Radarr hold an
empty one. That was left alone: setting a password on Deluge would break both
arrs until their stored credentials were updated too.