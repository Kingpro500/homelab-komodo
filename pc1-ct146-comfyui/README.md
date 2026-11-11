# ComfyUI med modell for voksent innhold på pc1 (CT146)

- **Node:** pc1 · **IP:** `10.0.0.221` · **Web:** http://10.0.0.221:8188 (ComfyUI)
- **Modell:** Krea2 NSFW-mix (`Quiho/Krea2_NSFW_Uncensored_Complete`: moodyKrea2Mix v3 FP8, abliterated tekstenkoder, VAE)
- **GPU:** RTX 3070 8 GB, delt med de andre pc1-CT-ene (FLUX CT144, ollama CT156/350). Kjør bare én om gangen; ComfyUI startes med `--lowvram`.
- **Deploy:** Komodo-stack fra `docker-compose.yml`. Containeren kjører `/models/start.sh` (kopi av `start.sh` her), som ved første start installerer ComfyUI + venv og laster modellene til `/models`, og hopper over det som finnes.
- **Lagring:** `/models` er Tower (`/mnt/pve/Tower-isos/comfyui`): ComfyUI, venv, modeller og `output/` (bilder). Ingenting av dette ligger i Git.
- **Visning:** galleri som i CT144 på http://IP:7860 (kjapp = turbo-LoRA, 6 steg; bedre = full modell, 20 steg; standard 1920x1080; bilder i `/models/gallery`). ComfyUI selv på :8188.
- **Oppgradering:** `git pull` i `/models/ComfyUI` + redeploy; modellene byttes ved å endre URL i `start.sh`.
- **Merk:** Modellen er laget for voksent innhold; tilgang bare fra LAN.
