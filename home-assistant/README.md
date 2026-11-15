# pc1 boot choice for Home Assistant

Copy `pc1-boot-choice.yaml` into the Home Assistant packages/configuration setup and copy the three shell scripts into `/config/scripts/` with executable permissions. The package exposes two scripts: Windows 11 and Proxmox. Each selection sets the next UEFI boot entry on pc1 with `efibootmgr`, then reboots pc1.

The implementation deliberately keeps SSH credentials and host-key material outside Git. It requires Home Assistant to have an existing, restricted SSH path to `root@pc1`; no token, password, or key is configured here.

The fixed UEFI entries are:

- `0000`: Windows 11
- `0002`: Proxmox

The target host must be checked once with `efibootmgr -v` before enabling the package, because firmware entry numbering is hardware state. The control only checks that the published implementation contains both documented entry numbers and the `efibootmgr` call.
