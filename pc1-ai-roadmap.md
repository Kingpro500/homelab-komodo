# pc1 AI and automation roadmap

Status: **utdatert — omskrevet 4. oktober 2026.** Dokumentet beskrev en plan
som aldri ble realisert. Den opprinnelige versjonen la Hermes på pc1 med
Ollama som modellleverandør. Verken det eller Ollama på GPU har skjedd.

## Hva som faktisk kjører i dag

| Tjeneste | Hvor | Merknad |
| --- | --- | --- |
| Hermes Agent | CT157 på **pc6**, `10.0.0.135:9119` | Ikke pc1. Egen Komodo-stack, persistent `/opt/data`. |
| Modell | `anthropic/claude-haiku-4.5` via **OpenRouter** | Lokal modell er ikke i bruk og er ikke satt opp som fallback. |
| Ollama | CT156 på **pc1**, `10.0.0.133:11434` | Kjører på CPU. Svarer HTTP 200, v0.35.0, modell `qwen3:4b`. |
| n8n | CT103, `10.0.0.119:5678` | CT103 fysisk på pc6, ikke pc1. |
| Open WebUI | CT103, `10.0.0.119:3080` | Peker på `OLLAMA_BASE_URL=http://10.0.0.133:11434`. |

## Hvorfor Ollama aldri fikk GPU-en

pc1 dual-booter Windows 11 og Proxmox. RTX 3070-en er fysisk til stede —
verifisert via PCI som `GA104 [GeForce RTX 3070]`, vendor `0x10de`, device
`0x2484` — men NVIDIA-driveren er ikke lastet når Proxmox kjører. Derfor:

- CT156 mapper `dev0`–`dev4` til `/dev/nvidia0`, `/dev/nvidiactl`,
  `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`, `/dev/nvidia-modeset`.
- Hver `vzstart` siden 2. oktober feiler med `Device /dev/nvidia0 does not exist`.
- Resultat: `qwen3:4b` kjører på CPU. Målt 5,1 s for ett token, inkludert
  lasting fra disk. `/api/ps` er tom mellom forespørsler.

Dette er ikke en Komodo-feil. Komodo-agenten i CT156 kjører ikke i det hele
tatt, så Komodo viser serveren rød uansett — men Ollama selv svarer og er
operasjonelt frisk.

## Konflikten som må løses først

pc1 har 8 GB RAM og dual-booter Windows. Det gir et eksklusivitetsproblem:

- Windows startet → Proxmox er nede, ingen CT-er, ingen GPU tilgjengelig for CT.
- Proxmox startet → ingen Windows, men GPU-avhengigheten ovenfor gjelder.

Får du den ene eller den andre, ikke begge. Ethvert lokalt LLM-oppsett må
regnes som eksklusivt med Windows-booten.

## Alternativer

**A — Lokalt LLM på pc1.** Installer NVIDIA-driveren på Proxmox, og bytt
`dev0`–`dev4` mot `lxc.cgroup2.devices.allow` (nåværende config bruker
VM-syntax `dev<n>=path=` på en unprivileged LXC, som ikke virker). Dette
løser også driverkonflikten mellom Windows og Proxmox, eller flytter den.
Resultat: en 4B-modell på en 3070 i stedet for sekunder per token.

**B — Bare OpenRouter.** Slett CT156. Open WebUI må pekes et annet sted eller
tas ned, ellers står den igjen som tom chat-klient. Frigjør 12,5 GiB disk på
pc1 og lukker en CRITICAL-alert som har stått åpen siden 1. oktober.

**Valget er ikke tatt.** Ingen endringer gjort på pc1 per 4. oktober 2026.

## Guardrails som fortsatt gjelder

- Ikke installer Ollama med GPU-førventning før `nvidia-smi` virker på
  pc1-Proxmox-verten.
- Hold modellfiler på CT156-disken, ikke på Tower-mediedeler.
- n8n må bruke persistent runtime-data og PostgreSQL i egen Komodo-stack;
  aldri workflow-legitimasjon i Git.
- Credentials hører hjemme i Komodo-secrets, aldri i Git eller shell-historikk.
- Ikke mount Docker-socket, SSH-nøkler, Codex deploy-nøkkel eller
  mediedeler inn i Hermes. Scope er bare egen CT.
- Reserver DHCP-adresser først etter CT-opprettelse og MAC-verifisering.

## Observasjoner

- `pc1-ct156-ollama` står rød i Komodo siden agenten ikke kjører. Skill
  «Komodo NotOk» fra «tjeneste nede» — disse er uavhengige.
- pc1 har ingen Netdata-agent, så den mangler også i Cloud-dashbordet.
  pc6, pve, pc9 og Unraid Tower har alle agent på port 19999.
- Brukt VMID: 100–104, 106, 109–111, 115, 116, 151–157. Ledig fra 117.