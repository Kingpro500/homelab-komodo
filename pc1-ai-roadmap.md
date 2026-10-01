# pc1 AI and automation roadmap

pc1 has 8 GB host RAM and an NVIDIA RTX 3070. Workloads are deliberately
separated so the GPU service, automation service and agent runtime can be
maintained independently through Komodo.

| Order | Planned workload | Proposed node | Resources | Dependency |
| --- | --- | --- | --- | --- |
| 1 | Ollama | Dedicated GPU CT on pc1 | 4 vCPU, 4 GB RAM, 32 GB disk, NVIDIA GPU | Install NVIDIA driver on pc1 first |
| 2 | n8n | Dedicated Docker / Komodo CT on pc1 | 2 vCPU, 2 GB RAM, 16 GB disk | Ollama endpoint only if a workflow uses it |
| 3 | Hermes Agent (Nous Research) | Dedicated Docker / Komodo CT on pc1 | 2 vCPU, 2 GB RAM, 20 GB disk initially | Ollama and an explicitly configured model provider |

## Guardrails

- Do not install Ollama until `nvidia-smi` works on the pc1 Proxmox host.
- Keep model files on the Ollama CT disk; do not place them on Tower media
  shares.
- n8n must use persistent runtime data and PostgreSQL in its own Komodo stack;
  never keep workflow credentials in Git.
- Hermes is the official Nous Research project (`nousresearch/hermes-agent`).
  It will use its own Komodo stack and persistent `/opt/data` mount for
  configuration, memory, sessions and skills; this state is never stored in
  Git.
- Do not mount a Docker socket, Proxmox/Tower SSH keys, the Codex GitHub deploy
  key, or media shares into Hermes. Its default scope is only its own CT.
- Keep the Hermes dashboard and OpenAI-compatible API private to the LAN (or
  SSH tunnel) initially. Do not enable Telegram, Discord, WhatsApp, or another
  messaging integration without a separate, explicit decision.
- Run `hermes setup` only after Ollama is working and we have chosen the model
  and gateway configuration. Provider/API credentials belong in Komodo secrets,
  never in Git or a shell history.
- Hermes can execute commands, browse, create skills and keep memory. Treat it
  as a separately administered agent, not as an unrestricted administrator of
  the homelab.
- Reserve DHCP addresses only after CT creation and MAC verification.
