# Reserve Emby

Deploy this Compose file through Komodo to the standby Docker server.

## Stack settings

- Run directory: `emby-backup`
- Compose file: `docker-compose.yml`

Configure the following variables in the Komodo Stack environment:

```dotenv
EMBY_CONFIG_PATH=<persistent config directory on the standby host>
EMBY_BACKUP_PATH=<local backup archive directory>
EMBY_TRANSCODE_PATH=<local transcode directory>
EMBY_MEDIA_PATH=<local offline media directory>
EMBY_LIBRARY_PATH=<matching path used by the primary Emby library>
```

The image version is pinned to match the primary Emby server. The media mount is read-only. Host networking keeps Emby's normal web and discovery ports available on the standby host.

Create the configured host directories with ownership matching `EMBY_UID` and `EMBY_GID` before deployment. Their defaults match the current installation and can be overridden in Komodo.

Use Emby's Backup & Restore plugin to transfer server configuration, users and user data. Keep a distinct Server ID while testing. Use the primary Server ID only during an actual failover after the primary server is shut down. Enter the Premiere key manually in Emby; do not store it in Git.

Hardware transcoding is omitted until the GPU device has been passed through and verified on the standby host.
