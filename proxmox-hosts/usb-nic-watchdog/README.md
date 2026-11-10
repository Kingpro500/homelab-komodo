# usb-nic-watchdog — USB-nettverksadapteren på pc7 og pc8

pc7 og pc8 har administrasjonsnettet (vmbr0, også CT-ene) på en USB 2.5G-adapter
(Realtek RTL8156, driver `r8152`). OPNsense på pc7 bruker de innebygde portene via passthrough
og påvirkes ikke av dette.

## Hva skjedde 10. nov 2026

- 20:56:26 `r8152 … nic4: Tx status -71` (USB-protokollfeil), 20:56:30 `USB disconnect`,
  20:56:31 adapteren koblet seg inn igjen som `nic4` — men ble **ikke lagt tilbake i vmbr0**.
  pc7 hadde link (blinket), men var borte til omstart kl. 22:45.
- Samme sekund stoppet trafikken ~3 s på pc8 (uten carrier-tap), og Roger fant en defekt nettverkskabel.
- Proxmox binder vmbr0 til adapterens navn på hver maskin, så adaptere kan ikke byttes mellom pc7 og pc8.

## To lag

| Fil | Installeres som | Gjør |
| --- | --- | --- |
| `90-usb-nic-rebridge.rules` | `/etc/udev/rules.d/` | Når en r8152-adapter kobler seg inn igjen: `ifreload -a` etter 5 s, så den legges tilbake i vmbr0 (dekker 10. nov-hendelsen) |
| `usb-nic-watchdog` + `.service` | `/usr/local/sbin/`, `/etc/systemd/system/` | Ingen svar fra OPNsense/ERX/pc6 i 30 s → USB-tilbakestilling (authorized 0/1) + `ifreload -a`. Maks 5/time, 120 s mellom forsøk, ingenting de første 3 min etter oppstart |

Bevislogg ved hver tilbakestilling: `/var/log/usb-nic-watchdog/<tid>.log` (link-status + kjernelogg).
Hendelse sendes til n8n `/webhook/events` når nettet er tilbake. `DRY_RUN=1` for test uten å røre adapteren.

Installert og aktiv på **pc7** og **pc8** (10. nov 2026). Ekte tilbakestilling er ennå ikke testet.
