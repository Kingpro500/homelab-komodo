# pc6-ct143-crafty

Crafty Controller (Minecraft-administrasjon) i egen CT: **pc6 / CT143 / 10.0.0.218**, UI på `https://10.0.0.218:8000` (HTTPS).
Flyttet ut av media-CT-en CT210 (`pc6-ct109-crafty`), siden den ikke har noe med media å gjøre.

- Komodo-server `pc6-ct143-ct143`, stack `pc6-ct143-crafty`. CT 2 kjerner, 2,5 GB, 16 GB disk.
- Bildet er pinnet på digest. `cybercube/crafty-controller` har bare taggen `latest` (bygd 2021).
- Data i navngitt volum `crafty-data` (`/home/crafty`). Det ble flyttet fra CT210 11. nov 2026; ingen Minecraft-servere var konfigurert.
- Deploy kun via Komodo: PullStack → DeployStack.
