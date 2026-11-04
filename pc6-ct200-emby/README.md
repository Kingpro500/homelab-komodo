# Emby: primary and warm standby

## Topology

- **CT200 / PC6 / 10.0.0.150:8096** is the active, primary Emby server.
- **CT203 / PC9 / 10.0.0.127:8096** is a warm standby, deployed by Komodo as `pc9-ct203-emby-standby`.
- Both use the same Tower media export read-only; this remains a shared dependency.
- The servers never share `/config`, SQLite databases, or a server identity.

## Standby metadata policy

The standby uses its own small configuration and metadata directory. The primary metadata directory is not copied: it is about 61 GB, while CT203 has about 44 GB free. That policy also avoids carrying the primary SQLite databases into a second active server.

Primary inspection on 2026-11-04 found 10,957 BIF seek-preview files using about 37.01 GiB. Chapter-image extraction and thumbnail/seek-preview extraction must remain disabled for any library later configured on CT203. No BIF files have been deleted from the primary.

## Playback and failover

Failover is controlled, not seamless: active viewers must reconnect to CT203. Existing HLS streams cannot migrate between independent Emby servers. Never start recovery by mounting the primary `/config` directory read-write on CT203.

## Configuration backup

CT200 runs `/usr/local/sbin/emby-config-backup` daily at 04:15 (with 15 minutes randomized delay), managed by `emby-config-backup.timer`. It writes a compact, consistent backup to:

`/media/Emby Backup/ct200-config-snapshots/`

The backup contains SQLite `.backup` exports, configuration, plugins, a manifest and hashes. It deliberately excludes metadata, BIF previews, cache, logs and transcodes. The requested `/mnt/user/appdata/backup` is not exported by Unraid; the established writable Emby Backup location is used instead.

An isolated restore drill on CT203 on 2026-11-04 copied the newest snapshot to temporary local storage, validated the archive and all database hashes, checked the SQLite file signatures, and removed only the temporary test directory. It did not start a second Emby process or alter CT200.

## Tower NFS mount authority

`Tower-media` is owned by Proxmox cluster storage configuration at `/etc/pve/storage.cfg`. It uses NFSv4 and is bound read-only into Emby/Tunarr containers. On PC6, a competing legacy `/etc/fstab` entry using a soft NFS mount was disabled on 2026-11-04 after a dated backup of `fstab` was made under `/root/config-backups/`.

Do not add a second fstab mount for `/mnt/pve/Tower-media`. A competing mount definition can race with Proxmox/systemd automount handling after reboot and worsen stale-file-handle recovery.

## Verify

```sh
systemctl status emby-config-backup.timer
systemctl start emby-config-backup.service
```

Restore only with the primary Emby container stopped, and only after selecting a specific dated snapshot.
