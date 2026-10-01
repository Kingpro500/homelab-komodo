# Ollama on pc1 CT 156

- **Host:** pc1 (`10.0.0.112`)
- **LXC:** `pc1-ct156-ollama`
- **IP:** `10.0.0.133`
- **GPU:** NVIDIA RTX 3070 (8 GB VRAM)
- **API:** `http://10.0.0.133:11434`

This stack is deployed only through Komodo. Models and Ollama state persist at
`/opt/ollama` inside the LXC and are deliberately not committed to Git or
copied to Tower.

The LXC receives only the NVIDIA device nodes required by this workload. The
host NVIDIA driver and Docker GPU runtime were validated before deployment.

## Capacity profile

pc1 has 8 GB of host RAM. CT 103 (the generic Docker node) is intentionally
stopped with autostart disabled while this CT runs. Start only one of those
profiles until the host gets more RAM.
