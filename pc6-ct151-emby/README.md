# Emby on CT 151

This stack migrates the existing Tower Emby server to the `emby-pc6` Proxmox container. It uses the official Emby image, host networking, the restored Emby program data, the Tower media share with write access, and Intel Quick Sync through `renderD128`.

Deploy it through Komodo on the `emby-pc6` server with these Stack variables:

```dotenv
EMBY_CONFIG_PATH=/opt/emby/EmbyServer
EMBY_TRANSCODE_PATH=/opt/emby/transcode
EMBY_MEDIA_PATH=/media
EMBY_LIBRARY_PATH=/mnt
EMBY_UID=2
EMBY_GID=2
EMBY_GIDLIST=2,44
TZ=Europe/Oslo
MALLOC_TRIM_THRESHOLD_=131072
```

The `/media` mount is deliberately writable. Emby needs that access to keep NFO metadata and artwork next to the media. The container path `/mnt` matches the library paths from the restored Emby database.

Before the first deployment, create the local transcode directory on CT 151:

```bash
install -d -o 2 -g 2 -m 0755 /opt/emby/transcode
```

Do not stop or remove the old Tower Emby server until this stack is healthy, libraries load correctly, and a hardware-transcode test succeeds.
