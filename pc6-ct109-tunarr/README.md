# Tunarr — pc6 CT109

- **Komodo server / stack:** `pc6-ct109-node` / `pc6-ct109-tunarr`
- **Web UI:** `http://10.0.0.128:8005`

Tunarr builds live TV channels out of media you already own. It works by adding a
spoofed HDHomeRun tuner to Emby, so Emby sees a set of channels rather than a
library. It also exposes a plain M3U URL for IPTV players such as Tivimate or
UHF — those need no Emby connection at all.

Media stays where it is. Tunarr does not move or copy anything: it points at the
Emby library and streams from it.

## Ports

The image exposes `8000/tcp` and `1900/udp`. Both are published:

- **8000/tcp → host 8005.** The image's own default, 8000, is already taken by
  Crafty Controller on this node.
- **1900/udp → host 1900.** SSDP discovery, which is how Tunarr finds Emby on the
  LAN by itself. Without it the Emby connection must be added manually; nothing
  breaks either way.

## Media source

Emby is at `http://10.0.0.150:8096` on CT151, called "Tower Emby", version
4.10.0.40. Its library is mounted over **NFS from Tower Unraid**
(`10.0.0.101:/mnt/user/media`), so Tunarr only needs to reach Emby — no media
mount of its own.

Tunarr needs an Emby account with access to the libraries being turned into
channels. Create a dedicated user in Emby rather than reusing the admin one, so
Tunarr can be revoked independently later.

## Channels, not a library

Tunarr adds a spoofed HDHomeRun tuner to Emby, so Emby shows a channel lineup
rather than its library, and it also serves a plain M3U URL that IPTV players
such as Tivimate or UHF can open directly — those need no Emby connection at
all.

Media stays where it is. Tunarr neither moves nor copies anything: it points at
the Emby library and streams from it. Emby's own library sits over NFS from Tower
Unraid, so Tunarr needs only network access to Emby, not a media mount.

## Config

State lives in the named volume `tunarr-config` at `/config`. The image declares
no `VOLUME` and runs as root, so the path was confirmed by inspecting the image
rather than assumed.