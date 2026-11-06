# UISP

Komodo-managed UISP for EdgeSwitch/EdgeMAX administration on PC9/CT124.

- Host: `pc9-ct124-uisp` (`10.0.0.17`)
- URL after deployment: `https://10.0.0.17/`
- Image: `nico640/docker-unms:3.1.70` (third-party packaging; not Ubiquiti-supported)
- Persistent state: `./data`

Deploy only through Komodo. Do not run this compose file manually. UISP setup
credentials and device credentials belong in its UI or protected runtime state,
never in this repository.
