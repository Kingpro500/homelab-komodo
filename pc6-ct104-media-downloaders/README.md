# MeTube on CT 123

This Komodo stack runs MeTube on CT 123 (`10.0.0.229`).

Pinchflat moved to the dedicated CT 172 (`10.0.0.164`) and is managed by the
`pc6-ct172-pinchflat` Komodo stack. Do not add Pinchflat back to this Compose
file; its database workload previously exhausted CT 120 memory and swap.

Media stays on Tower. Proxmox mounts the Tower media NFS export on the pc6 host
and bind-mounts it into CT 123 at `/media`. MeTube uses
`/media/metube` directly. MeTube cookies were copied from CT 120 to the CT 123
local disk at `/opt/metube/Cookies`; the backup remains on pc6 at
`/root/metube-cookies-before-ct123.tar`.

Deploy through Komodo with these variables:

```dotenv
METUBE_COOKIES_PATH=/opt/metube/Cookies
TOWER_MEDIA_PATH=/media
TZ=Europe/Oslo
```

MeTube is published at `http://10.0.0.229:8081`. Its Komodo stack is named
`pc6-ct123-metube` and belongs to server `pc6-ct123-ct123`. The Compose project
(`media-downloaders`) and repository run directory (`pc6-ct104-media-downloaders`)
retain their historical names to avoid an unnecessary recreation.

Pinchflat documentation and Compose configuration are in
`pc6-ct172-pinchflat/`.
