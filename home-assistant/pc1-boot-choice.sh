#!/bin/sh
set -eu

# Called on Home Assistant. The SSH key and host-key trust are managed on HA;
# no credentials are stored in this repository.
entry="$1"
case "$entry" in
  0000|0002) ;;
  *) echo "invalid EFI boot entry" >&2; exit 2 ;;
esac

ssh -o BatchMode=yes -o ConnectTimeout=10 root@pc1 "efibootmgr -n $entry && systemctl reboot"
