# Media automation on pc6 CT 109

One Komodo stack on the shared Docker node `pc6-ct109-node` (`10.0.0.128`).
It contains Bazarr, Prowlarr, Sonarr, Radarr, Readarr and Podgrab.

| Service | Address |
| --- | --- |
| Bazarr | `http://10.0.0.128:6767` |
| Prowlarr | `http://10.0.0.128:9696` |
| Sonarr | `http://10.0.0.128:8989` |
| Radarr | `http://10.0.0.128:7878` |
| Readarr | `http://10.0.0.128:8787` |
| Podgrab | `http://10.0.0.128:8081` |

Runtime configuration is copied from Tower to `/opt/media-automation`; media
and downloads stay on Tower. The CT has a dedicated RW bind mount at `/data`,
which maps to Tower's `media` share. Audiobookshelf remains separate within the
same CT and uses its existing read-only `/scan/media` bind mount.

Required Komodo variable:

```text
MEDIA_AUTOMATION_CONFIG_ROOT=/opt/media-automation
```
