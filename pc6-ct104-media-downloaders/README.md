# Media downloaders on CT 104

This Komodo stack runs Pinchflat and MeTube on `pc6` in CT 104 (`10.0.0.124`).

Media stays on Tower. Proxmox mounts the Tower media NFS export on the pc6 host and bind-mounts it into CT 104 at `/media`. The services use the existing `/media/YouTube` and `/media/metube` directories directly. Only the following application state is copied from Tower to the CT local disk:

- Pinchflat: `/mnt/user/appdata/pinchflat` to `/opt/pinchflat`
- MeTube cookies: `/mnt/user/media/metube/Cookies` to `/opt/metube/Cookies`

Deploy through Komodo with these global variables:

```dotenv
PINCHFLAT_CONFIG_PATH=/opt/pinchflat
METUBE_COOKIES_PATH=/opt/metube/Cookies
TOWER_MEDIA_PATH=/media
TZ=Europe/Oslo
```

The services are published on the CT IP:

- Pinchflat: `http://10.0.0.124:8945`
- MeTube: `http://10.0.0.124:8081`

Do not remove the stopped Tower containers or their local configuration until both CT 104 services have been verified with a real download.
