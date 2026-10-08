# Media players, legacy Tower migration

CT107 on pc6 temporarily hosts the old Tower Jellyfin and Plex containers.
It is deliberately configured with `onboot: 0`; its Tower media mount is
read-only and it is shut down after migration verification.
