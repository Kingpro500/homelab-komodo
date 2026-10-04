# MySpeed and DiskSpeed on CT 104

The services run on `pc6`, CT 104 (`10.0.0.124`).

- MySpeed: `http://10.0.0.124:5216`
- DiskSpeed: `http://10.0.0.124:8888`

Komodo variables:

```dotenv
MYSPEED_DATA_PATH=/opt/myspeed
DISKSPEED_DATA_PATH=/opt/diskspeed
TZ=Europe/Oslo
```

MySpeed state is migrated from Tower. DiskSpeed is a new independent instance: its former Tower setup depended on Unraid's local `/var/local/emhttp` mount, so the new service measures CT 104 / pc6 storage rather than Tower disks.
