# Oppskrift: Ny Docker-CT med Komodo Periphery

Denne oppskriften beskriver den fungerende metoden for å koble en ny Proxmox LXC-container til Komodo Core på `10.0.0.117:9120`.

Metoden bruker direkte Core → Periphery-tilkobling med en tilfeldig passkey. Den er laget for dagens Komodo-oppsett, der offentlig-nøkkelmetoden i Komodo 2.3.3 ga valideringsfeil selv når nøkkelhashene var identiske.

## Variabler

Bytt ut disse verdiene for hver ny CT:

```text
CT_ID=<ledig VMID>
CT_NAME=<navn, for eksempel ct111-ntfy>
KOMODO_SERVER_NAME=<navn, for eksempel pc9-ct111-ntfy>
CT_IP=<ledig statisk IP>
PROXMOX_NODE=pc9
KOMODO_CORE_IP=10.0.0.117
```

## 1. Opprett CT

Anbefalt minimum for en liten Docker-tjeneste:

```text
OS: Debian 12
Disk: 8 GB
CPU: 1 kjerne
RAM: 1024 MB
Swap: 512 MB
Bridge: vmbr0
Gateway: 10.0.0.1
Unprivileged: ja
On boot: ja
Features: nesting=1,keyctl=1
```

Eksempel:

```bash
pct create "$CT_ID" local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname "$CT_NAME" \
  --cores 1 \
  --memory 1024 \
  --swap 512 \
  --rootfs local-lvm:8 \
  --net0 "name=eth0,bridge=vmbr0,firewall=1,gw=10.0.0.1,ip=${CT_IP}/24,type=veth" \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --onboot 1 \
  --start 1
```

Kontroller at IP-adressen er ledig før CT-en opprettes.

## 2. Installer Docker og Compose v2

Kjør i CT-en:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates curl docker.io
systemctl enable --now docker
```

Komodo bruker kommandoen `docker compose`. Kontroller derfor at Compose v2 finnes:

```bash
docker compose version
```

`docker-compose` v1 alene er ikke tilstrekkelig. Installer Compose-pluginen dersom kommandoen mangler. I dette miljøet finnes en fungerende plugin på eksisterende Komodo-noder under:

```text
/usr/libexec/docker/cli-plugins/docker-compose
```

Installer pluginen i samme bane i den nye CT-en og kontroller på nytt:

```bash
chmod 755 /usr/libexec/docker/cli-plugins/docker-compose
docker compose version
```

## 3. Generer en unik passkey

Generer en ny passkey for hver CT:

```bash
openssl rand -hex 32
```

Lagre verdien sikkert. Den samme verdien skal konfigureres både i Periphery og i Komodo-serverressursen.

Ikke skriv passkey-en i logger, dokumentasjon eller Git.

## 4. Installer Periphery

Opprett katalogen:

```bash
mkdir -p /opt/komodo/periphery
```

Opprett `/opt/komodo/periphery/periphery.env`:

```dotenv
PERIPHERY_SERVER_ENABLED=true
PERIPHERY_PASSKEYS=<PASSKEY_FRA_FORRIGE_STEG>
PERIPHERY_ROOT_DIRECTORY=/opt/komodo
```

Sett sikre filrettigheter:

```bash
chmod 600 /opt/komodo/periphery/periphery.env
```

Opprett `/opt/komodo/periphery/docker-compose.yml`:

```yaml
services:
  komodo-periphery:
    image: ghcr.io/moghtech/komodo-periphery:2.3.3
    container_name: komodo-periphery
    restart: unless-stopped
    init: true
    env_file:
      - periphery.env
    ports:
      - "8120:8120"
    volumes:
      - /opt/komodo:/opt/komodo
      - periphery-keys:/config/keys
      - /var/run/docker.sock:/var/run/docker.sock
      - /proc:/proc

volumes:
  periphery-keys:
```

Start Periphery:

```bash
cd /opt/komodo/periphery
docker compose up -d
```

## 5. Ikke aktiver reverse connection

Denne oppskriften bruker bare direkte Core → Periphery-tilkobling.

Ikke sett disse variablene:

```text
PERIPHERY_CORE_ADDRESS
PERIPHERY_CORE_ADDRESSES
PERIPHERY_CONNECT_AS
PERIPHERY_CORE_PUBLIC_KEYS
PERIPHERY_PRIVATE_KEY
```

Hvis direkte og reverse modus brukes samtidig, kan Komodo opprette to forbindelser med samme servernavn. Det gir meldingen:

```text
Only one Server connected as '<servernavn>' is allowed
```

## 6. Verifiser Periphery lokalt

Kontroller containeren:

```bash
docker ps --filter name=komodo-periphery
docker logs --tail 50 komodo-periphery
```

Kontroller TLS-porten:

```bash
curl -k -o /dev/null -w '%{http_code}\n' https://127.0.0.1:8120/
```

En `400`-respons på den tomme forespørselen er forventet. Det bekrefter at Periphery lytter med TLS.

Hvis forbindelsen blir avvist eller er tom, kontroller at loggen viser:

```text
server_enabled: Some(true)
Server starting on https://[::]:8120
```

## 7. Legg inn avgrenset Proxmox-brannmurregel

Port 8120 skal kun være tilgjengelig fra Komodo Core:

```bash
pvesh create "/nodes/${PROXMOX_NODE}/lxc/${CT_ID}/firewall/rules" \
  --type in \
  --action ACCEPT \
  --source "${KOMODO_CORE_IP}/32" \
  --proto tcp \
  --dport 8120 \
  --enable 1 \
  --comment Komodo-Core-to-Periphery
```

Kontroller at regelen faktisk er aktiv:

```bash
pvesh get "/nodes/${PROXMOX_NODE}/lxc/${CT_ID}/firewall/rules" \
  --output-format json-pretty
```

Se spesielt etter:

```json
"enable": 1
```

Proxmox kan opprette en regel med `enable: 0` dersom `--enable 1` utelates.

## 8. Opprett serveren i Komodo

Opprett én serverressurs med følgende verdier:

```text
Name: <KOMODO_SERVER_NAME>
Address: https://<CT_IP>:8120
External address: http://<CT_IP>
Enabled: true
Insecure TLS: true
Passkey: <samme passkey som PERIPHERY_PASSKEYS>
Public key: tom
Region: pc9
```

Viktig:

- `public_key` må være tom når passkey brukes.
- Hvis en offentlig nøkkel er satt, forsøker Komodo nøkkelautentisering før passkey.
- `insecure_tls` kreves fordi Periphery genererer et selvsignert TLS-sertifikat.

Kontroller at serverstatus i Komodo blir:

```text
Ok
```

Ikke opprett eller deploy applikasjonsstacken før serverstatus er `Ok`.

## 9. Test fra Komodo Core

Kjør fra Core-CT-en:

```bash
curl -k -o /dev/null -w '%{http_code}\n' "https://${CT_IP}:8120/"
```

Forventet resultat er `400`.

Hvis porten ikke kan nås:

1. Kontroller `PERIPHERY_SERVER_ENABLED=true`.
2. Kontroller `docker ps` og portmapping `8120:8120`.
3. Kontroller at Proxmox-regelen har `enable: 1`.
4. Kontroller at regelen tillater Core-IP-en, ikke bare Proxmox-verten.
5. Kontroller lokalt med `curl -k https://127.0.0.1:8120/`.

## 10. Opprett og deploy stacken

Når Komodo-serverstatus er `Ok`, opprett stacken og velg den nye serveren.

For ntfy ble denne Compose-filen brukt:

```yaml
services:
  ntfy:
    image: binwiederhier/ntfy:v2
    container_name: ntfy
    command: serve
    restart: unless-stopped
    environment:
      NTFY_BASE_URL: http://10.0.0.131
      NTFY_CACHE_FILE: /var/cache/ntfy/cache.db
      NTFY_AUTH_FILE: /var/lib/ntfy/auth.db
    ports:
      - "80:80"
    volumes:
      - ntfy-cache:/var/cache/ntfy
      - ntfy-data:/var/lib/ntfy

volumes:
  ntfy-cache:
  ntfy-data:
```

Tilpass `NTFY_BASE_URL` til den nye CT-ens IP.

## 11. Åpne applikasjonsporten på LAN

For ntfy på port 80:

```bash
pvesh create "/nodes/${PROXMOX_NODE}/lxc/${CT_ID}/firewall/rules" \
  --type in \
  --action ACCEPT \
  --source 10.0.0.0/24 \
  --proto tcp \
  --dport 80 \
  --enable 1 \
  --comment LAN-to-ntfy
```

Bruk alltid smalest mulig kilde og port for andre tjenester.

## 12. Sluttkontroll

Kontroller containere:

```bash
docker ps
```

For ntfy skal både disse kjøre:

```text
komodo-periphery
ntfy
```

Kontroller ntfy lokalt:

```bash
curl -o /dev/null -w '%{http_code}\n' http://127.0.0.1/
```

Kontroller fra LAN eller Proxmox-verten:

```bash
curl -o /dev/null -w '%{http_code}\n' "http://${CT_IP}/"
```

Forventet resultat:

```text
200
```

Kontroller loggen:

```bash
docker logs --tail 50 ntfy
```

For ntfy skal den blant annet vise:

```text
Listening on :80[http]
```

## Kort sjekkliste

- [ ] Ledig VMID og IP er kontrollert.
- [ ] CT bruker `nesting=1,keyctl=1`.
- [ ] Docker kjører.
- [ ] `docker compose version` fungerer.
- [ ] Unik 256-bits passkey er generert.
- [ ] Passkey finnes både i Periphery og Komodo.
- [ ] `PERIPHERY_SERVER_ENABLED=true` er satt.
- [ ] Reverse connection-variabler er ikke satt.
- [ ] Periphery lytter på TLS-port 8120.
- [ ] Port 8120 er kun tillatt fra Komodo Core-IP-en.
- [ ] Brannmurreglene har `enable: 1`.
- [ ] Komodo-serveren har tom `public_key`.
- [ ] Komodo-serverstatus er `Ok`.
- [ ] Applikasjonsstacken er deployet gjennom Komodo.
- [ ] Applikasjonens HTTP-test gir forventet statuskode.

## Kjente feil og årsaker

### `Core failed to validate Periphery public key`

Komodo forsøker fortsatt offentlig-nøkkelautentisering. Tøm `public_key` på serverressursen når passkey-metoden brukes.

### Port 8120 er publisert, men svarer ikke

Periphery-servermodusen er sannsynligvis deaktivert. Sett:

```text
PERIPHERY_SERVER_ENABLED=true
```

### Core når ikke port 8120

Kontroller at Proxmox-brannmurregelen er aktivert og tillater Core-IP-en.

### `Only one Server connected as ... is allowed`

Både direkte og reverse connection er aktivert. Fjern reverse connection-variablene og behold bare direkte modus.

### Komodo sier `Cannot send command when Server is unreachable or disabled`

Ikke deploy stacken ennå. Rett Periphery-tilkoblingen og vent til serverstatus er `Ok`.

