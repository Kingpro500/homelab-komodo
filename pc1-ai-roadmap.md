# pc1 AI and automation roadmap

pc1 has 8 GB host RAM and an NVIDIA RTX 3070. Workloads are deliberately
separated so the GPU service, automation service and agent runtime can be
maintained independently through Komodo.

| Order | Planned workload | Proposed node | Resources | Dependency |
| --- | --- | --- | --- | --- |
| 1 | Ollama | Dedicated GPU CT on pc1 | 4 vCPU, 4 GB RAM, 32 GB disk, NVIDIA GPU | Install NVIDIA driver on pc1 first |
| 2 | n8n | Dedicated Docker / Komodo CT on pc1 | 2 vCPU, 2 GB RAM, 16 GB disk | Ollama endpoint only if a workflow uses it |
| 3 | Hermes agent | Dedicated Docker / Komodo CT on pc1 | Reserve a small node; size after identifying the exact project | Ollama API, if supported by the selected Hermes project |

## Guardrails

- Do not install Ollama until `nvidia-smi` works on the pc1 Proxmox host.
- Keep model files on the Ollama CT disk; do not place them on Tower media
  shares.
- n8n must use persistent runtime data and PostgreSQL in its own Komodo stack;
  never keep workflow credentials in Git.
- Confirm the exact Hermes agent repository/image before deployment. Several
  unrelated projects use the name “Hermes”; this avoids deploying the wrong
  software or giving it unnecessary access.
- Reserve DHCP addresses only after CT creation and MAC verification.
