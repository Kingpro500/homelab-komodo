# pc8-ct142-crafty

Crafty Controller (Minecraft-administrasjon) i egen CT: **pc8 / CT142 / 10.0.0.217**, UI på `http://10.0.0.217:8000`.
Flyttet ut av media-CT-en CT210 (`pc6-ct109-crafty`), siden den ikke har noe med media å gjøre.

- Komodo-server `pc8-ct142-crafty`, stack `pc8-ct142-crafty` (opprettet med `ct-new`).
- Bildet er pinnet på digest. `cybercube/crafty-controller` har bare taggen `latest` (bygd 2021).
- Data i navngitt volum `crafty-data` (`/home/crafty`). Det ble flyttet fra CT210 11. nov 2026; ingen Minecraft-servere var konfigurert.
- Deploy kun via Komodo: PullStack → DeployStack.
