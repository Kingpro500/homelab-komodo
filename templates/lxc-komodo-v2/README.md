# Docker LXC + Komodo V2 template

Use this template for each new Docker workload that belongs in an isolated
Proxmox LXC. It is based on the working CT 104 and CT 152 setup.

## Naming

- **Komodo server:** `pc6-ct153-immich`
- **Komodo stack / repository directory:** `pc6-ct153-immich`
- **LXC hostname:** a short service name, for example `immich`.

The name is `host` + `ct` + `workload`. The IP belongs in the description and
README, not in the resource name; it can then change without a rename.

## Proxmox baseline

Create an unprivileged Debian LXC with a fixed LAN address. Required options:

```text
unprivileged: 1
features: nesting=1,keyctl=1
net0: bridge=vmbr0,firewall=1,gw=10.0.0.1,ip=10.0.0.X/24
```

Use 2 CPU / 4 GB RAM as a small default; size storage and memory for the
workload. Add GPU devices and Tower mounts only when the application needs
them. Media stays on Tower and is mounted into the CT; it is never copied.

## Bootstrap once

1. Install Docker and the Compose implementation used by the CT.
2. Create `/opt/komodo/periphery/` and copy `periphery-compose.yml` to
   `/opt/komodo/periphery-compose.yml`.
3. Copy Core's public key to `/opt/komodo/periphery/core.pub` (read-only for
   the container). This is required for reconnects after a Core restart.
4. Create `/opt/komodo/periphery/.env` from `periphery.env.example`, replacing
   only the CT address. This file is private runtime state and is not in Git.
5. Create a **short-lived V2** onboarding key in Komodo and append it as
   `PERIPHERY_ONBOARDING_KEY` temporarily.
6. Start Periphery with:

   ```sh
   cd /opt/komodo
   docker-compose --env-file periphery/.env -f periphery-compose.yml up -d
   ```

7. Confirm that the new server is `OK` in Komodo. Remove the onboarding key
   from `.env`, delete the onboarding key in Komodo, then recreate Periphery
   using the same command. The `periphery-data` volume preserves its identity.
8. Add the application stack in Git and deploy it through Komodo. Do not start
   the application with a separate, unmanaged Compose command.

## Guardrails

- Never commit `.env`, API credentials, onboarding keys, database passwords,
  application databases, uploads, or media.
- Never remove `periphery-data` for routine repairs or upgrades. It changes the
  server identity and requires a new V2 onboarding flow.
- If a restored node fails only after Core restarts, compare its Periphery
  public-key fingerprint with the server record. Repair a mismatch with a
  short-lived **privileged V2 onboarding key**; do not replace the volume.
- Before retiring Tower containers, validate the new service and keep the old
  service stopped as rollback until acceptance.
