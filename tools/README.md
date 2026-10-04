# tools

## check_homepage.py

Verifies that every service in `homepage/config/services.yaml` still points at a
guest (or node, router, or VM) that exists in Proxmox with the CT/VM number and
node recorded correctly.

A link drifts when a container is recreated, gets a new address, or moves to
another host. That happened here twice: Emby changed IP, and n8n moved from pc1
to pc6. Nothing broke, but the Homepage described systems that no longer
existed in that form.

```
python3 tools/check_homepage.py
```

Prints one line per mismatch and exits with `Avvik: N`. Zero means every entry
resolves.

Exit code is always 0, so it is safe to run from a schedule and parse the output
instead. It only reads Proxmox; it never changes anything.

Credentials come from `PROXMOX_URL`, `PROXMOX_TOKEN_ID` and
`PROXMOX_TOKEN_SECRET`, read from the environment or from the dotenv file at
`~/.hermes/.env`. Override the file with `HOMELAB_ENVFILE`.
