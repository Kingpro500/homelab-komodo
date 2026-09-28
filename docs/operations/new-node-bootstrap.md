# New-node bootstrap

Use this procedure for every new Linux node that should allow Codex diagnostics.

1. Keep `ops/fleet/install-codex-readonly.sh` in the private homelab repository.
2. On the new node, log in as root through the normal administrative channel.
3. Copy the file to `/root/install-codex-readonly.sh` and run:

   ```bash
   bash /root/install-codex-readonly.sh
   ```

4. Confirm that it ends with `parsed OK` and `Codex restricted diagnostic access installed.`
5. Add the node to `docs/operations/node-inventory.md`, then verify it with `ssh codex@NODE health` from the Codex host.

## What the installer permits

The resulting SSH key cannot open a terminal, forward ports, use the Docker socket directly, read arbitrary files, install packages, restart services, or modify the host. It can only run:

- `health`
- `docker-status`
- `docker-logs <container>`
- `systemd <unit.service>`

To revoke access, remove `/home/codex/.ssh/authorized_keys` or delete the `codex` account.
