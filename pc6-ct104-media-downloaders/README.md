# Media downloaders on CT 120

This Komodo stack now runs MeTube on CT 120 (`10.0.0.124`).

Pinchflat moved to the dedicated CT 172 (`10.0.0.164`) and is managed by the
`pc6-ct172-pinchflat` Komodo stack. Do not add Pinchflat back to this Compose
file; its database workload previously exhausted CT 120 memory and swap.

Media stays on Tower. Proxmox mounts the Tower media NFS export on the pc6 host
and bind-mounts it into CT 120 at `/media`. MeTube uses
`/media/metube` directly. MeTube cookies remain on the CT local disk at
`/opt/metube/Cookies`.

Deploy through Komodo with these variables:

```dotenv
METUBE_COOKIES_PATH=/opt/metube/Cookies
TOWER_MEDIA_PATH=/media
TZ=Europe/Oslo
```

MeTube is published at `http://10.0.0.124:8081`.

Pinchflat documentation and Compose configuration are in
`pc6-ct172-pinchflat/`.
